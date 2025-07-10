"""
EDUCATIONAL PURPOSES ONLY - UPDATED VERSION

WARNING: Using this code violates Discord's Terms of Service and can result in your account being permanently banned.
This script is provided for educational purposes only to understand the differences between bot accounts and user accounts.
DO NOT use this code with your personal Discord account.

This updated version attempts to work around some Discord restrictions.
"""

import aiohttp
import asyncio
import json
import logging
import os
import re
import sys
import time
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration (with environment variable support)
SOURCE_CHANNEL_ID = int(os.environ.get('SOURCE_CHANNEL_ID', '1386133052148944960'))  # The ID of the channel to read from
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', "https://discord.com/api/webhooks/1392768773068423239/n2atDpXB40sFhJ5jJosMRSsJEcMV8ViocYXiLbTMCoiCw-FmDr_vs-aY-j-LtIQCBE32")  # The webhook URL to send to
USER_TOKEN = os.environ.get('USER_TOKEN', "")  # ⚠️ Your token - blank by default for security

# Source and destination server IDs (for role mention mapping)
SOURCE_SERVER_ID = os.environ.get('SOURCE_SERVER_ID', "1386133051276570650")  # Source server ID
DESTINATION_SERVER_ID = os.environ.get('DESTINATION_SERVER_ID', "1392768772153077881")  # Destination server ID

# Role mention handling
ALWAYS_CONVERT_ROLE_MENTIONS_TO_TEXT = os.environ.get('ALWAYS_CONVERT_ROLE_MENTIONS_TO_TEXT', 'False').lower() == 'true'  # Set to False to use role mappings for proper mentions

# Optional role ID mapping - will be used if role_map.json exists
ROLE_ID_MAP = {}

# API Constants
API_VERSION = 9
BASE_URL = f"https://discord.com/api/v{API_VERSION}"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"

# Role cache to avoid fetching roles for every message
SERVER_ROLES_CACHE = {}

class LowLevelDiscordClient:
    def __init__(self, token):
        self.token = token
        self.session = None
        self.headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/channels/@me"
        }
        self.last_message_id = None
    
    async def initialize(self):
        self.session = aiohttp.ClientSession()
        # Verify token works by getting user info
        user_data = await self.get_user_me()
        if not user_data:
            logger.error("Failed to authenticate with Discord. Token may be invalid.")
            return False
        logger.info(f"Logged in as {user_data.get('username')}#{user_data.get('discriminator')} (ID: {user_data.get('id')})")
        return True
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    async def get_user_me(self):
        try:
            async with self.session.get(f"{BASE_URL}/users/@me", headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error getting user info: {response.status}")
                    logger.error(await response.text())
                    return None
        except Exception as e:
            logger.error(f"Exception in get_user_me: {str(e)}")
            return None
    
    async def get_channel_messages(self, channel_id, limit=10):
        url = f"{BASE_URL}/channels/{channel_id}/messages?limit={limit}"
        if self.last_message_id:
            url += f"&after={self.last_message_id}"
        
        try:
            async with self.session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    messages = await response.json()
                    if messages and len(messages) > 0:
                        self.last_message_id = messages[0]["id"]
                    return messages
                else:
                    logger.error(f"Error getting messages: {response.status}")
                    logger.error(await response.text())
                    return []
        except Exception as e:
            logger.error(f"Exception in get_channel_messages: {str(e)}")
            return []
    
    async def download_attachment(self, url):
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.error(f"Error downloading attachment: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Exception in download_attachment: {str(e)}")
            return None
    
    async def send_webhook_message(self, webhook_url, content, username, avatar_url=None, embeds=None, files=None):
        data = {
            "content": content,
            "username": username,
        }
        
        if avatar_url:
            data["avatar_url"] = avatar_url
        
        if embeds:
            data["embeds"] = embeds
        
        try:
            form = aiohttp.FormData()
            payload_json = json.dumps(data)
            form.add_field('payload_json', payload_json, content_type='application/json')
            
            if files:
                for i, file_data in enumerate(files):
                    form.add_field(f'file{i}', file_data['data'], 
                                 filename=file_data['filename'],
                                 content_type='application/octet-stream')
            
            async with self.session.post(webhook_url, data=form) as response:
                if response.status in [200, 204]:
                    return True
                else:
                    logger.error(f"Error sending webhook: {response.status}")
                    logger.error(await response.text())
                    return False
        except Exception as e:
            logger.error(f"Exception in send_webhook_message: {str(e)}")
            return False

async def cache_server_roles(client, guild_id):
    """Fetch and cache all roles from a server"""
    global SERVER_ROLES_CACHE
    
    if not guild_id:
        logger.error("Cannot cache roles: No guild ID provided")
        return {}
    
    # Skip fetching if we already have issues with this server
    if guild_id in SERVER_ROLES_CACHE and SERVER_ROLES_CACHE[guild_id] == {}:
        logger.warning(f"Skipping role fetch for server {guild_id} - previously failed")
        return {}
    
    logger.info(f"Fetching and caching roles from server {guild_id}")
    roles_url = f"{BASE_URL}/guilds/{guild_id}/roles"
    
    try:
        async with client.session.get(roles_url, headers=client.headers) as response:
            if response.status == 200:
                roles_data = await response.json()
                # Create a map of role ID to role name
                roles_map = {str(role["id"]): role["name"] for role in roles_data}
                SERVER_ROLES_CACHE[guild_id] = roles_map
                
                # Print all roles for debugging
                logger.info(f"Cached {len(roles_map)} roles from server {guild_id}")
                for role_id, role_name in roles_map.items():
                    logger.info(f"  - Role: {role_name} (ID: {role_id})")
                
                # Create a simple manual mapping file if it doesn't exist
                if not os.path.exists("manual_role_map.json"):
                    with open("manual_role_map.json", "w") as f:
                        sample_mapping = {}
                        for role_id, role_name in roles_map.items():
                            sample_mapping[role_id] = ""  # Empty destination ID, to be filled by user
                        json.dump(sample_mapping, f, indent=2)
                    logger.info("Created manual_role_map.json template - you can fill in destination role IDs")
                
                return roles_map
            else:
                error_text = await response.text()
                logger.error(f"Error fetching roles from server {guild_id}: {response.status}")
                logger.error(error_text)
                
                # Cache an empty dict to prevent repeated failed requests
                SERVER_ROLES_CACHE[guild_id] = {}
                
                # Still use the role mapping even if we can't fetch roles directly
                logger.info("Will rely on role_map.json for role mapping instead of direct API access")
                return {}
    except Exception as e:
        logger.error(f"Exception in cache_server_roles: {str(e)}")
        # Cache an empty dict to prevent repeated failed requests
        SERVER_ROLES_CACHE[guild_id] = {}
        return {}

async def replace_role_mentions(client, content):
    """Replace role mentions in content with role names or mapped role IDs"""
    # Detect role mentions with regex
    role_pattern = r'<@&(\d+)>'
    role_mentions = re.findall(role_pattern, content)
    
    if not role_mentions:
        return content
    
    # If we found role mentions, use our role mappings from role_map.json
    for role_id in role_mentions:
        # Check if we have a mapping for this role in ROLE_ID_MAP
        if role_id in ROLE_ID_MAP:
            # We have a mapping, use it to replace with destination role mention
            dest_role_id = ROLE_ID_MAP[role_id]
            content = content.replace(f'<@&{role_id}>', f'<@&{dest_role_id}>')
            logger.info(f"Replaced role ID {role_id} with destination role ID {dest_role_id}")
            continue
        
        # No mapping found, try to get role name from cache first
        role_name = None
        for server_id, roles in SERVER_ROLES_CACHE.items():
            if role_id in roles:
                role_name = roles[role_id]
                logger.info(f"Found role name '{role_name}' for ID {role_id}")
                break
        
        # If not in cache, try to fetch it directly (only if we're configured to do so)
        if not role_name and SOURCE_SERVER_ID:
            try:
                logger.info(f"Role {role_id} not in cache, fetching directly")
                roles_url = f"{BASE_URL}/guilds/{SOURCE_SERVER_ID}/roles"
                async with client.session.get(roles_url, headers=client.headers) as response:
                    if response.status == 200:
                        roles_data = await response.json()
                        for role in roles_data:
                            if str(role['id']) == role_id:
                                role_name = role['name']
                                logger.info(f"Fetched role name '{role_name}' for ID {role_id}")
                                # Update cache
                                if SOURCE_SERVER_ID not in SERVER_ROLES_CACHE:
                                    SERVER_ROLES_CACHE[SOURCE_SERVER_ID] = {}
                                SERVER_ROLES_CACHE[SOURCE_SERVER_ID][role_id] = role_name
                                break
            except Exception as e:
                logger.error(f"Error fetching role info: {str(e)}")
        
        # If still not found, use "unknown-role"
        if not role_name:
            role_name = "unknown-role"
            logger.warning(f"Could not find name for role ID {role_id}, using '{role_name}'")
        
        # If configured to always use text or if we don't have a mapping
        if ALWAYS_CONVERT_ROLE_MENTIONS_TO_TEXT:
            # Always replace with text format
            content = content.replace(f'<@&{role_id}>', f'@{role_name}')
            logger.info(f"Replaced role ID {role_id} with text '@{role_name}'")
        else:
            # We're here because we didn't have a mapping for this role
            # So replace with text since we can't properly map the mention
            content = content.replace(f'<@&{role_id}>', f'@{role_name}')
            logger.info(f"Replaced role ID {role_id} with text '@{role_name}' (no mapping available)")
    
    return content

async def main():
    global ROLE_ID_MAP
    
    # Validate required environment variables
    if not USER_TOKEN:
        logger.error("USER_TOKEN is not set. Please set it in your environment variables.")
        return
    
    if not WEBHOOK_URL:
        logger.error("WEBHOOK_URL is not set. Please set it in your environment variables.")
        return
    
    # Load role mapping if it exists
    if os.path.exists("role_map.json"):
        try:
            with open("role_map.json", "r") as f:
                ROLE_ID_MAP = json.load(f)
            logger.info(f"Loaded role mapping for {len(ROLE_ID_MAP)} roles")
            
            # Print the first few mappings for debugging
            count = 0
            for source_id, dest_id in ROLE_ID_MAP.items():
                logger.info(f"Role mapping: {source_id} -> {dest_id}")
                count += 1
                if count >= 5:  # Just show a few examples
                    logger.info(f"... and {len(ROLE_ID_MAP) - 5} more mappings")
                    break
        except Exception as e:
            logger.error(f"Error loading role_map.json: {str(e)}")
    else:
        logger.warning("No role_map.json found! Role mentions will be converted to text.")
        logger.warning("Run fix_unknown_role_emergency.py first to create role mappings.")
    
    client = LowLevelDiscordClient(USER_TOKEN)
    
    try:
        success = await client.initialize()
        if not success:
            return
        
        logger.info(f"Monitoring channel {SOURCE_CHANNEL_ID}")
        
        # Get server ID from channel if not specified
        if not SOURCE_SERVER_ID:
            try:
                channel_info_url = f"{BASE_URL}/channels/{SOURCE_CHANNEL_ID}"
                async with client.session.get(channel_info_url, headers=client.headers) as response:
                    if response.status == 200:
                        channel_data = await response.json()
                        guild_id = channel_data.get("guild_id")
                        if guild_id:
                            logger.info(f"Detected source server ID: {guild_id}")
                            # Now get the roles once at startup
                            await cache_server_roles(client, guild_id)
            except Exception as e:
                logger.error(f"Error detecting server ID: {str(e)}")
        else:
            # Cache roles from source server at startup
            await cache_server_roles(client, SOURCE_SERVER_ID)
        
        # Also cache destination server roles if specified
        if DESTINATION_SERVER_ID:
            logger.info("Caching destination server roles")
            await cache_server_roles(client, DESTINATION_SERVER_ID)
            
        # Try to load manual role mapping if it exists
        if os.path.exists("manual_role_map.json"):
            try:
                with open("manual_role_map.json", "r") as f:
                    manual_map = json.load(f)
                    # Filter out empty mappings
                    valid_mappings = {k: v for k, v in manual_map.items() if v}
                    if valid_mappings:
                        logger.info(f"Loaded {len(valid_mappings)} manual role mappings")
                        # Update our global role map with these mappings
                        ROLE_ID_MAP.update(valid_mappings)
            except Exception as e:
                logger.error(f"Error loading manual role mappings: {str(e)}")
        
        while True:
            try:
                # Get messages
                messages = await client.get_channel_messages(SOURCE_CHANNEL_ID, limit=5)
                
                # Process messages (newest first)
                for message in reversed(messages):
                    content = message.get("content", "")
                    
                    # Replace role mentions with role names
                    content = await replace_role_mentions(client, content)
                    
                    username = message.get("author", {}).get("username", "Unknown")
                    avatar_url = message.get("author", {}).get("avatar")
                    if avatar_url:
                        avatar_url = f"https://cdn.discordapp.com/avatars/{message['author']['id']}/{avatar_url}.png"
                    
                    # Handle embeds
                    embeds = message.get("embeds", [])
                    
                    # Handle attachments
                    attachments = message.get("attachments", [])
                    files = []
                    for attachment in attachments:
                        file_data = await client.download_attachment(attachment.get("url"))
                        if file_data:
                            files.append({
                                "data": file_data,
                                "filename": attachment.get("filename", "file.dat")
                            })
                    
                    # Send to webhook
                    logger.info(f"Forwarding message from {username}")
                    await client.send_webhook_message(
                        WEBHOOK_URL,
                        content,
                        username,
                        avatar_url,
                        embeds,
                        files
                    )
                
                # Wait a bit before checking again
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                await asyncio.sleep(10)  # Wait longer if there's an error
    
    finally:
        await client.close()

if __name__ == "__main__":
    # Check for auto-run mode
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # Skip the warning in auto mode
        print("=" * 80)
        print("Starting Discord message forwarder in automatic mode...")
        print("=" * 80)
    else:
        # Final warning before running
        print("=" * 80)
        print("⚠️ WARNING: Using a user account for automation violates Discord's Terms of Service ⚠️")
        print("This can result in your account being permanently banned.")
        print("=" * 80)
        input("Press Enter to acknowledge this risk (or CTRL+C to cancel)... ")
    
    # Run the client
    asyncio.run(main())
