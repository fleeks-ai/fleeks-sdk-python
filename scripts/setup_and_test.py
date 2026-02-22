#!/usr/bin/env python3
"""
Fleeks SDK Setup and Test Script

This script helps you get started with the Fleeks SDK by:
1. Installing the SDK (if not already installed)
2. Prompting for your API key
3. Testing the connection to the Fleeks API
"""

import subprocess
import sys


def install_fleeks_sdk():
    """Install the Fleeks SDK from PyPI."""
    print("📦 Installing Fleeks SDK...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fleeks-sdk", "-q"])
        print("✅ Fleeks SDK installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Fleeks SDK: {e}")
        return False


def get_api_key():
    """Prompt the user for their Fleeks API key."""
    print("\n🔑 Fleeks API Key Setup")
    print("-" * 40)
    print("You can get your API key from: https://app.fleeks.ai/settings/api-keys")
    print()
    
    api_key = input("Enter your Fleeks API key: ").strip()
    
    if not api_key:
        print("❌ API key cannot be empty!")
        return None
    
    return api_key


def test_connection(api_key):
    """Test the connection to the Fleeks API."""
    print("\n🔗 Testing connection to Fleeks API...")
    
    try:
        from fleeks_sdk import FleeksClient
        
        client = FleeksClient(api_key=api_key)
        
        # Try to list workspaces as a simple connectivity test
        workspaces = client.workspaces.list()
        
        print("✅ Connection successful!")
        print(f"📁 Found {len(workspaces)} workspace(s)")
        
        if workspaces:
            print("\nYour workspaces:")
            for ws in workspaces[:5]:  # Show first 5
                name = getattr(ws, 'name', 'Unnamed')
                ws_id = getattr(ws, 'id', 'N/A')
                print(f"  • {name} (ID: {ws_id})")
            
            if len(workspaces) > 5:
                print(f"  ... and {len(workspaces) - 5} more")
        
        return True
        
    except ImportError:
        print("❌ Fleeks SDK not found. Please install it first.")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def save_api_key_instruction(api_key):
    """Show instructions for saving the API key."""
    print("\n💡 To save your API key for future use, set the environment variable:")
    print()
    print("   Windows (PowerShell):")
    print(f'   $env:FLEEKS_API_KEY = "{api_key}"')
    print()
    print("   Windows (Command Prompt):")
    print(f'   set FLEEKS_API_KEY={api_key}')
    print()
    print("   Linux/macOS:")
    print(f'   export FLEEKS_API_KEY="{api_key}"')
    print()
    print("   Or add it to your .env file:")
    print(f'   FLEEKS_API_KEY={api_key}')


def main():
    print("=" * 50)
    print("   🚀 Fleeks SDK Setup & Test Script")
    print("=" * 50)
    
    # Step 1: Install SDK
    install_choice = input("\nInstall/upgrade Fleeks SDK? (y/n) [y]: ").strip().lower()
    if install_choice != 'n':
        if not install_fleeks_sdk():
            print("\n⚠️  You can try installing manually with: pip install fleeks-sdk")
    
    # Step 2: Get API key
    api_key = get_api_key()
    if not api_key:
        print("\n❌ Setup cancelled - no API key provided.")
        sys.exit(1)
    
    # Step 3: Test connection
    if test_connection(api_key):
        save_api_key_instruction(api_key)
        print("\n" + "=" * 50)
        print("   ✅ Setup Complete! You're ready to use Fleeks SDK")
        print("=" * 50)
        
        print("\n📚 Quick Start Example:")
        print("-" * 40)
        print("""
from fleeks_sdk import FleeksClient

client = FleeksClient(api_key="your-api-key")

# Create a workspace
workspace = client.workspaces.create(name="My Project")

# Create an agent
agent = client.agents.create(
    workspace_id=workspace.id,
    name="my-agent",
    model="gpt-4"
)

# Send a message
response = agent.chat("Hello, how can you help me?")
print(response)
""")
    else:
        print("\n⚠️  Please check your API key and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
