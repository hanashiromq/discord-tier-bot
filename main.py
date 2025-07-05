import discord
from discord.ext import commands
import asyncio
import os
from database import Database
from bot_commands import TierCommands
from config import Config
from views_persistent import PersistentTierApplicationView, PersistentTierAssignmentView
from keep_alive import keep_alive

# Configure intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class TierBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        self.db = Database()
        
    async def setup_hook(self):
        # Initialize database
        await self.db.init_db()
        
        # Add cog
        await self.add_cog(TierCommands(self))
        
        # Restore persistent views
        await self.restore_persistent_views()
        
        # Sync commands
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Failed to sync commands: {e}")
    
    async def restore_persistent_views(self):
        """Restore persistent views after bot restart"""
        try:
            views_data = await self.db.get_persistent_views()
            restored_count = 0
            
            for view_data in views_data:
                try:
                    message_id = view_data['message_id']
                    channel_id = int(view_data['channel_id'])
                    view_type = view_data['view_type']
                    
                    channel = self.get_channel(channel_id)
                    if not channel:
                        # Channel not found, remove from database
                        await self.db.delete_persistent_view(message_id)
                        continue
                    
                    try:
                        message = await channel.fetch_message(int(message_id))
                    except discord.NotFound:
                        # Message deleted, remove from database
                        await self.db.delete_persistent_view(message_id)
                        continue
                    
                    # Create appropriate view
                    if view_type == "tier_assignment":
                        if view_data['view_data'] and 'application_id' in view_data['view_data']:
                            app_id = view_data['view_data']['application_id']
                            view = PersistentTierAssignmentView(app_id)
                        else:
                            continue
                    elif view_type == "tier_application":
                        view = PersistentTierApplicationView()
                    else:
                        continue
                    
                    # Attach view to message
                    self.add_view(view, message_id=int(message_id))
                    restored_count += 1
                    
                except Exception as e:
                    print(f"Error restoring view {view_data['message_id']}: {e}")
                    # Remove problematic view from database
                    await self.db.delete_persistent_view(view_data['message_id'])
            
            if restored_count > 0:
                print(f"Restored {restored_count} persistent view(s)")
                
        except Exception as e:
            print(f"Error restoring persistent views: {e}")
    
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guilds')
    
    async def close(self):
        """Called when the bot is shutting down"""
        await self.db.close()
        await super().close()

async def main():
    # Start keep_alive server
    keep_alive()
    
    # Уведомление о запуске
    print("[BOT] Starting Discord Tier Bot with monitoring...")
    print(f"[BOT] Keep-alive server: http://0.0.0.0:8080")
    print(f"[BOT] Monitor endpoints: /status, /health")
    
    bot = TierBot()
    
    # Get token from environment
    token = os.getenv('DISCORD_TOKEN')
    print(f"[DEBUG] Token from env length: {len(token) if token else 0}")
    
    # If token is empty or too short, try to read from file
    if not token or len(token.strip()) < 50:  # Discord tokens are ~70 chars
        print("WARNING: DISCORD_TOKEN is empty or invalid, trying to read from token.txt file...")
        try:
            with open('token.txt', 'r') as f:
                token = f.read().strip()
                print(f"[DEBUG] Token from file length: {len(token) if token else 0}")
        except FileNotFoundError:
            print("ERROR: No token.txt file found")
        except Exception as e:
            print(f"ERROR: Could not read token.txt: {e}")
    
    if not token or len(token.strip()) < 50:
        print("ERROR: DISCORD_TOKEN not found or too short")
        print("Please either:")
        print("1. Set DISCORD_TOKEN in Secrets tab")
        print("2. Create token.txt file with your Discord bot token")
        return
    
    print(f"[DEBUG] Using token with length: {len(token)}")
    
    try:
        await bot.start(token)
    except Exception as e:
        print(f"Error starting bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
