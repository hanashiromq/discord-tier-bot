#!/usr/bin/env python3
import os

print("Testing token reading...")

# Test reading from file
try:
    with open('token.txt', 'r') as f:
        token_from_file = f.read().strip()
        print(f"Token from file length: {len(token_from_file)}")
        print(f"Token from file first 20 chars: {token_from_file[:20]}")
        print(f"Token from file last 20 chars: {token_from_file[-20:]}")
except Exception as e:
    print(f"Error reading file: {e}")

# Test environment variable
env_token = os.getenv('DISCORD_TOKEN')
print(f"Token from env length: {len(env_token) if env_token else 0}")

# Test if they match
if env_token and token_from_file:
    print(f"Tokens match: {env_token == token_from_file}")