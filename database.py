import aiosqlite
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any

class Database:
    def __init__(self, db_path: str = "tier_bot.db"):
        self.db_path = db_path
        
    async def init_db(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Players table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id TEXT UNIQUE NOT NULL,
                    game_id TEXT NOT NULL,
                    game_nickname TEXT NOT NULL,
                    current_clan TEXT,
                    page_info TEXT,
                    tier TEXT DEFAULT 'None',
                    tier_assigned_at TIMESTAMP,
                    tier_assigned_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Applications table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    game_nickname TEXT NOT NULL,
                    current_clan TEXT,
                    page_info TEXT,
                    desired_tier TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    message_id TEXT,
                    channel_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    processed_by TEXT
                )
            ''')
            
            # Tier assignments log
            await db.execute('''
                CREATE TABLE IF NOT EXISTS tier_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id TEXT NOT NULL,
                    old_tier TEXT,
                    new_tier TEXT NOT NULL,
                    assigned_by TEXT NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    application_id INTEGER,
                    FOREIGN KEY (application_id) REFERENCES applications (id)
                )
            ''')
            
            # Guild settings
            await db.execute('''
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id TEXT PRIMARY KEY,
                    applications_channel_id TEXT,
                    tier_roles TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Persistent views table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS persistent_views (
                    message_id TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    view_type TEXT NOT NULL,
                    view_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
    
    async def create_application(self, discord_id: str, game_id: str, game_nickname: str, 
                               current_clan: str, page_info: str, desired_tier: str) -> int:
        """Create a new tier application"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO applications (discord_id, game_id, game_nickname, current_clan, page_info, desired_tier)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (discord_id, game_id, game_nickname, current_clan, page_info, desired_tier))
            await db.commit()
            return cursor.lastrowid or 0
    
    async def get_application(self, app_id: int) -> Optional[Dict[str, Any]]:
        """Get application by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM applications WHERE id = ?', (app_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def update_application_status(self, app_id: int, status: str, processed_by: str = None):
        """Update application status"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE applications 
                SET status = ?, processed_at = CURRENT_TIMESTAMP, processed_by = ?
                WHERE id = ?
            ''', (status, processed_by or "", app_id))
            await db.commit()
    
    async def assign_tier(self, discord_id: str, new_tier: str, assigned_by: str, application_id: int = None):
        """Assign tier to player"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get current player info
            cursor = await db.execute('SELECT * FROM players WHERE discord_id = ?', (discord_id,))
            row = await cursor.fetchone()
            old_tier = row[0] if row else None
            
            # Get application info if provided
            game_id = "N/A"
            game_nickname = "N/A"
            current_clan = "N/A"
            page_info = "N/A"
            
            if application_id:
                app_cursor = await db.execute('SELECT * FROM applications WHERE id = ?', (application_id,))
                app_row = await app_cursor.fetchone()
                if app_row:
                    # app_row format: (id, discord_id, game_id, game_nickname, current_clan, page_info, ...)
                    game_id = app_row[2] or "N/A"
                    game_nickname = app_row[3] or "N/A"
                    current_clan = app_row[4] or "N/A"
                    page_info = app_row[5] or "N/A"
            
            # Update or insert player with all required fields
            await db.execute('''
                INSERT OR REPLACE INTO players 
                (discord_id, game_id, game_nickname, current_clan, page_info, tier, tier_assigned_at, tier_assigned_by, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, CURRENT_TIMESTAMP)
            ''', (discord_id, game_id, game_nickname, current_clan, page_info, new_tier, assigned_by))
            
            # Log assignment
            await db.execute('''
                INSERT INTO tier_assignments (discord_id, old_tier, new_tier, assigned_by, application_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (discord_id, old_tier, new_tier, assigned_by, application_id))
            
            await db.commit()
    
    async def get_tier_leaderboard(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get tier leaderboard"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT discord_id, game_nickname, tier, tier_assigned_at,
                       CASE tier
                           WHEN 'T1' THEN 1
                           WHEN 'T2' THEN 2
                           WHEN 'T3' THEN 3
                           WHEN 'T4' THEN 4
                           WHEN 'T5' THEN 5
                           ELSE 6
                       END as tier_order
                FROM players 
                WHERE tier IS NOT NULL AND tier != 'None'
                ORDER BY tier_order ASC, tier_assigned_at ASC
                LIMIT ?
            ''', (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_player_by_discord_id(self, discord_id: str) -> Optional[Dict[str, Any]]:
        """Get player by Discord ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM players WHERE discord_id = ?', (discord_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def has_pending_application(self, discord_id: str) -> bool:
        """Check if user has pending application"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT COUNT(*) FROM applications 
                WHERE discord_id = ? AND status = 'pending'
            ''', (discord_id,))
            count = await cursor.fetchone()
            return count[0] > 0
    
    async def set_guild_applications_channel(self, guild_id: str, channel_id: str):
        """Set applications channel for guild"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO guild_settings (guild_id, applications_channel_id, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (guild_id, channel_id))
            await db.commit()
    
    async def get_guild_applications_channel(self, guild_id: str) -> Optional[str]:
        """Get applications channel for guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT applications_channel_id FROM guild_settings WHERE guild_id = ?
            ''', (guild_id,))
            row = await cursor.fetchone()
            return row[0] if row else None
    
    async def set_guild_tierlist_channel(self, guild_id: str, channel_id: str, message_id: str = None):
        """Set tierlist channel and message for guild"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO guild_settings 
                (guild_id, applications_channel_id, tier_list_channel_id, tier_list_message_id, updated_at)
                VALUES (
                    ?, 
                    COALESCE((SELECT applications_channel_id FROM guild_settings WHERE guild_id = ?), ?),
                    ?, ?, CURRENT_TIMESTAMP
                )
            ''', (guild_id, guild_id, channel_id, channel_id, message_id))
            await db.commit()
    
    async def get_guild_tierlist_info(self, guild_id: str) -> Optional[Dict[str, str]]:
        """Get tierlist channel and message info for guild"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT tier_list_channel_id, tier_list_message_id FROM guild_settings WHERE guild_id = ?
            ''', (guild_id,))
            row = await cursor.fetchone()
            if row:
                return {
                    'channel_id': row[0],
                    'message_id': row[1]
                }
            return None
    
    async def set_guild_allowed_roles(self, guild_id: str, role_ids: List[str]):
        """Set roles that can use the bot"""
        role_ids_str = ','.join(role_ids) if role_ids else None
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO guild_settings 
                (guild_id, applications_channel_id, tier_list_channel_id, tier_list_message_id, allowed_roles, admin_roles, updated_at)
                VALUES (
                    ?, 
                    COALESCE((SELECT applications_channel_id FROM guild_settings WHERE guild_id = ?), NULL),
                    COALESCE((SELECT tier_list_channel_id FROM guild_settings WHERE guild_id = ?), NULL),
                    COALESCE((SELECT tier_list_message_id FROM guild_settings WHERE guild_id = ?), NULL),
                    ?,
                    COALESCE((SELECT admin_roles FROM guild_settings WHERE guild_id = ?), NULL),
                    CURRENT_TIMESTAMP
                )
            ''', (guild_id, guild_id, guild_id, guild_id, role_ids_str, guild_id))
            await db.commit()
    
    async def set_guild_admin_roles(self, guild_id: str, role_ids: List[str]):
        """Set roles that can assign tiers"""
        role_ids_str = ','.join(role_ids) if role_ids else None
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO guild_settings 
                (guild_id, applications_channel_id, tier_list_channel_id, tier_list_message_id, allowed_roles, admin_roles, updated_at)
                VALUES (
                    ?, 
                    COALESCE((SELECT applications_channel_id FROM guild_settings WHERE guild_id = ?), NULL),
                    COALESCE((SELECT tier_list_channel_id FROM guild_settings WHERE guild_id = ?), NULL),
                    COALESCE((SELECT tier_list_message_id FROM guild_settings WHERE guild_id = ?), NULL),
                    COALESCE((SELECT allowed_roles FROM guild_settings WHERE guild_id = ?), NULL),
                    ?,
                    CURRENT_TIMESTAMP
                )
            ''', (guild_id, guild_id, guild_id, guild_id, guild_id, role_ids_str))
            await db.commit()
    
    async def get_guild_allowed_roles(self, guild_id: str) -> List[str]:
        """Get roles that can use the bot"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT allowed_roles FROM guild_settings WHERE guild_id = ?
            ''', (guild_id,))
            row = await cursor.fetchone()
            if row and row[0]:
                return row[0].split(',')
            return []
    
    async def get_guild_admin_roles(self, guild_id: str) -> List[str]:
        """Get roles that can assign tiers"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT admin_roles FROM guild_settings WHERE guild_id = ?
            ''', (guild_id,))
            row = await cursor.fetchone()
            if row and row[0]:
                return row[0].split(',')
            return []
    
    async def save_persistent_view(self, message_id: str, channel_id: str, guild_id: str, 
                                 view_type: str, view_data: dict = None):
        """Save persistent view data"""
        async with aiosqlite.connect(self.db_path) as db:
            current_time = int(datetime.now().timestamp())
            import json
            view_data_json = json.dumps(view_data) if view_data else None
            
            await db.execute('''
                INSERT OR REPLACE INTO persistent_views 
                (message_id, channel_id, guild_id, view_type, view_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (message_id, channel_id, guild_id, view_type, view_data_json, current_time))
            await db.commit()

    async def get_persistent_views(self) -> List[Dict[str, Any]]:
        """Get all persistent views for restoration"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT * FROM persistent_views ORDER BY created_at DESC
            ''')
            rows = await cursor.fetchall()
            
            result = []
            for row in rows:
                import json
                view_data = {
                    'message_id': row[0],
                    'channel_id': row[1], 
                    'guild_id': row[2],
                    'view_type': row[3],
                    'view_data': json.loads(row[4]) if row[4] else None,
                    'created_at': row[5]
                }
                result.append(view_data)
            return result

    async def delete_persistent_view(self, message_id: str):
        """Delete persistent view"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                DELETE FROM persistent_views WHERE message_id = ?
            ''', (message_id,))
            await db.commit()
    
    async def close(self):
        """Close database connection (for SQLite, this is a no-op)"""
        pass
    

