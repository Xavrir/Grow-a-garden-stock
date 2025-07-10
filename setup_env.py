"""
Environment Variable Setup Helper

This script helps you set up your environment variables for deployment.
It creates a .env file that you can use locally, and also provides
instructions for setting up variables on Railway.app.
"""

import os
import getpass

def create_env_file():
    print("=" * 70)
    print("Discord Forwarder Environment Setup")
    print("=" * 70)
    print("This will help you set up environment variables for your Discord forwarder.")
    print("The values you enter will be saved to a local .env file.")
    print("DO NOT commit this file to GitHub!")
    print()
    
    # Get user input
    source_channel_id = input("Enter SOURCE_CHANNEL_ID: ")
    webhook_url = input("Enter WEBHOOK_URL: ")
    user_token = getpass.getpass("Enter USER_TOKEN (input will be hidden): ")
    source_server_id = input("Enter SOURCE_SERVER_ID: ")
    dest_server_id = input("Enter DESTINATION_SERVER_ID: ")
    
    convert_mentions = input("Convert role mentions to text? (y/n, default: n): ").lower() == 'y'
    
    # Create .env file
    with open(".env", "w") as f:
        f.write(f"SOURCE_CHANNEL_ID={source_channel_id}\n")
        f.write(f"WEBHOOK_URL={webhook_url}\n")
        f.write(f"USER_TOKEN={user_token}\n")
        f.write(f"SOURCE_SERVER_ID={source_server_id}\n")
        f.write(f"DESTINATION_SERVER_ID={dest_server_id}\n")
        f.write(f"ALWAYS_CONVERT_ROLE_MENTIONS_TO_TEXT={'True' if convert_mentions else 'False'}\n")
    
    print("\n.env file created successfully!")
    print("For Railway.app deployment, make sure to set these same variables")
    print("in your Railway project settings under the Variables tab.")
    
    print("\nTo test locally with your .env file, you can use:")
    print("pip install python-dotenv")
    print("Then add this at the top of your Python script:")
    print("from dotenv import load_dotenv\nload_dotenv()")

if __name__ == "__main__":
    create_env_file()
