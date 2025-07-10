"""
Emergency Fix for @unknown-role Issues in Discord Forwarding

This script directly fixes role mention issues by creating an exact mapping between
source and destination servers based on role names.

It will:
1. Fetch all roles from both servers
2. Create a mapping based on matching role names
3. Save this mapping for the forwarding script to use
4. Optionally make destination roles mentionable
"""

import aiohttp
import asyncio
import json
import logging
import os
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration - Environment variables with fallbacks
SOURCE_SERVER_ID = os.environ.get('SOURCE_SERVER_ID', "")  # Source server ID
DESTINATION_SERVER_ID = os.environ.get('DESTINATION_SERVER_ID', "")  # Destination server ID
USER_TOKEN = os.environ.get('USER_TOKEN', "")  # Your token
MAKE_ROLES_MENTIONABLE = os.environ.get('MAKE_ROLES_MENTIONABLE', 'True').lower() == 'true'  # Set to True to make all roles mentionable

# API Constants
API_VERSION = 9
BASE_URL = f"https://discord.com/api/v{API_VERSION}"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"

async def get_roles(session, headers, guild_id):
    """Get all roles from a server"""
    url = f"{BASE_URL}/guilds/{guild_id}/roles"
    
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                roles = await response.json()
                # Filter out @everyone role
                roles = [r for r in roles if r["name"] != "@everyone"]
                return roles
            else:
                logger.error(f"Error fetching roles from {guild_id}: {response.status}")
                error_text = await response.text()
                logger.error(f"Response: {error_text}")
                return []
    except Exception as e:
        logger.error(f"Exception getting roles for {guild_id}: {str(e)}")
        return []

async def update_role(session, headers, guild_id, role_id, properties):
    """Update a role's properties (like making it mentionable)"""
    url = f"{BASE_URL}/guilds/{guild_id}/roles/{role_id}"
    
    try:
        async with session.patch(url, headers=headers, json=properties) as response:
            if response.status == 200:
                updated_role = await response.json()
                logger.info(f"Updated role {updated_role['name']}")
                return updated_role
            else:
                logger.error(f"Error updating role {role_id}: {response.status}")
                error_text = await response.text()
                logger.error(f"Response: {error_text}")
                return None
    except Exception as e:
        logger.error(f"Exception updating role {role_id}: {str(e)}")
        return None

async def fix_unknown_role_issue():
    """Main function to fix unknown role issues"""
    
    # Validate config
    if not SOURCE_SERVER_ID:
        logger.error("SOURCE_SERVER_ID not set. Please set it in your environment variables or at the top of the script.")
        return
    
    if not DESTINATION_SERVER_ID:
        logger.error("DESTINATION_SERVER_ID not set. Please set it in your environment variables or at the top of the script.")
        return
    
    if not USER_TOKEN:
        logger.error("USER_TOKEN not set. Please set it in your environment variables or at the top of the script.")
        return
    
    # Set up headers
    headers = {
        "Authorization": USER_TOKEN,
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "Origin": "https://discord.com",
        "Referer": "https://discord.com/channels/@me"
    }
    
    async with aiohttp.ClientSession() as session:
        # Get roles from both servers
        logger.info(f"Fetching roles from source server {SOURCE_SERVER_ID}...")
        source_roles = await get_roles(session, headers, SOURCE_SERVER_ID)
        
        logger.info(f"Fetching roles from destination server {DESTINATION_SERVER_ID}...")
        dest_roles = await get_roles(session, headers, DESTINATION_SERVER_ID)
        
        if not source_roles or not dest_roles:
            logger.error("Failed to fetch roles from one or both servers.")
            return
        
        logger.info(f"Found {len(source_roles)} roles in source server and {len(dest_roles)} roles in destination server")
        
        # Print all roles for reference
        print("\nSOURCE SERVER ROLES:")
        for role in source_roles:
            color_hex = f"#{role['color']:06x}" if role['color'] else "No color"
            print(f"  {role['name']} (ID: {role['id']}, Color: {color_hex})")
        
        print("\nDESTINATION SERVER ROLES:")
        for role in dest_roles:
            color_hex = f"#{role['color']:06x}" if role['color'] else "No color"
            print(f"  {role['name']} (ID: {role['id']}, Color: {color_hex})")
        
        # Create role mappings based on name
        role_map = {}
        missing_roles = []
        
        for source_role in source_roles:
            found = False
            for dest_role in dest_roles:
                if source_role["name"] == dest_role["name"]:
                    role_map[source_role["id"]] = dest_role["id"]
                    found = True
                    logger.info(f"Mapped {source_role['name']}: {source_role['id']} -> {dest_role['id']}")
                    
                    # Make role mentionable if needed
                    if MAKE_ROLES_MENTIONABLE and not dest_role.get("mentionable", False):
                        logger.info(f"Making role {dest_role['name']} mentionable...")
                        await update_role(session, headers, DESTINATION_SERVER_ID, dest_role["id"], {
                            "mentionable": True
                        })
                        await asyncio.sleep(0.5)  # Avoid rate limits
                    
                    break
            
            if not found:
                missing_roles.append(source_role["name"])
        
        # Save the role mapping
        with open("role_map.json", "w") as f:
            json.dump(role_map, f, indent=2)
        logger.info(f"Saved role mapping with {len(role_map)} entries to role_map.json")
        
        # Also save as manual_role_map.json for the other script
        with open("manual_role_map.json", "w") as f:
            json.dump(role_map, f, indent=2)
        logger.info(f"Saved role mapping to manual_role_map.json as well")
        
        # Report results
        print("\n=== ROLE MAPPING COMPLETE ===")
        print(f"Successfully mapped {len(role_map)} roles between servers")
        
        if missing_roles:
            print(f"\nWARNING: {len(missing_roles)} roles from source server were not found in destination server:")
            for role_name in missing_roles:
                print(f"  - {role_name}")
            print("\nYou may need to create these roles in your destination server!")
        else:
            print("\nAll roles from source server were found in destination server!")
        
        print("\n=== NEXT STEPS ===")
        print("1. Make sure role_map.json is in the same folder as direct_account_api.py")
        print("2. Restart your direct_account_api.py script")
        print("3. This should fix the @unknown-role issue for properly mapped roles")
        print("\nIf you're still having issues:")
        print("- Make sure your destination server allows webhooks to mention roles")
        print("- Try using text-based mentions by setting ALWAYS_CONVERT_ROLE_MENTIONS_TO_TEXT=True")
        print("  in direct_account_api.py or as an environment variable")

if __name__ == "__main__":
    print("=" * 70)
    print("Emergency Fix for @unknown-role Issues")
    print("This script will create a direct mapping between source and destination roles")
    print("=" * 70)
    
    # Check if running in auto mode
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        asyncio.run(fix_unknown_role_issue())
    else:
        input("Press Enter to continue (or CTRL+C to cancel)...")
        asyncio.run(fix_unknown_role_issue())
