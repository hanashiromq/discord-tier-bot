#!/usr/bin/env python3
import os
import sys

print("Testing Discord token access...")
token = os.getenv('DISCORD_TOKEN')
print(f"Token exists: {token is not None}")
print(f"Token length: {len(token) if token else 0}")

if token:
    print("Token starts with:", token[:10] + "..." if len(token) > 10 else token)
else:
    print("No token found!")
    print("Available environment variables:")
    for key in sorted(os.environ.keys()):
        if 'DISCORD' in key.upper() or 'TOKEN' in key.upper():
            print(f"  {key}: {len(os.environ[key])} chars")