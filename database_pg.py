import asyncpg
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

class PostgreSQLDatabase:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.pool = None

    async def init_db(self):
        """Initialize database connection pool and tables"""
        self.pool = await asyncpg.create_pool(self.db_url)

        async with self.pool.acquire() as conn:
            # Create tables
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    discord_id TEXT PRIMARY KEY,
                    game_id TEXT NOT NULL,
                    game_nickname TEXT NOT NULL,
                    current_clan TEXT,
                    page_info TEXT,
                    tier TEXT DEFAULT 'None',
                    tier_assigned_at BIGINT,
                    tier_assigned_by TEXT,
                    created_at BIGINT DEFAULT EXTRACT(epoch FROM NOW()),
                    updated_at BIGINT DEFAULT EXTRACT(epoch FROM NOW())
                )
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id SERIAL PRIMARY KEY,
                    discord_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    game_nickname TEXT NOT NULL,
                    current_clan TEXT,
                    page_info TEXT,
                    desired_tier TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    message_id TEXT,
                    channel_id TEXT,
                    created_at BIGINT DEFAULT EXTRACT(epoch FROM NOW()),
                    processed_at BIGINT,
                    processed_by TEXT
                )
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS tier_assignments (
                    id SERIAL PRIMARY KEY,
                    discord_id TEXT NOT NULL,
                    old_tier TEXT,
                    new_tier TEXT NOT NULL,
                    assigned_by TEXT NOT NULL,
                    assigned_at BIGINT DEFAULT EXTRACT(epoch FROM NOW()),
                    application_id INTEGER
                )
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id TEXT PRIMARY KEY,
                    applications_channel_id TEXT,
                    tier_list_channel_id TEXT,
                    tier_list_message_id TEXT,
                    allowed_roles TEXT,
                    admin_roles TEXT,
                    created_at BIGINT DEFAULT EXTRACT(epoch FROM NOW()),
                    updated_at BIGINT DEFAULT EXTRACT(epoch FROM NOW())
                )
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS persistent_views (
                    id SERIAL PRIMARY KEY,
                    message_id TEXT UNIQUE NOT NULL,
                    channel_id TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    view_type TEXT NOT NULL,
                    view_data JSONB,
                    created_at BIGINT DEFAULT EXTRACT(epoch FROM NOW())
                )
            ''')

    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()

    async def create_application(self, discord_id: str, game_id: str, game_nickname: str, 
                               current_clan: str, page_info: str, desired_tier: str) -> int:
        """Create a new tier application"""
        async with self.pool.acquire() as conn:
            current_time = int(datetime.now().timestamp())

            query = """
                INSERT INTO applications 
                (discord_id, game_id, game_nickname, current_clan, page_info, desired_tier, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """
            result = await conn.fetchrow(query, discord_id, game_id, game_nickname, current_clan, page_info, desired_tier, current_time)

            return result['id']

    async def get_application(self, app_id: int) -> Optional[Dict[str, Any]]:
        """Get application by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT * FROM applications WHERE id = $1
            ''', app_id)

            return dict(row) if row else None

    async def update_application_status(self, app_id: int, status: str, processed_by: str = None):
        """Update application status"""
        async with self.pool.acquire() as conn:
            current_time = int(datetime.now().timestamp())

            await conn.execute('''
                UPDATE applications 
                SET status = $1, processed_at = $2, processed_by = $3
                WHERE id = $4
            ''', status, current_time, processed_by, app_id)

    async def assign_tier(self, discord_id: str, new_tier: str, assigned_by: str, application_id: int = None):
        """Assign tier to player"""
        async with self.pool.acquire() as conn:
            current_time = int(datetime.now().timestamp())

            # Get current tier
            current_player = await conn.fetchrow('''
                SELECT tier FROM players WHERE discord_id = $1
            ''', discord_id)

            old_tier = current_player['tier'] if current_player else None

            # Update or create player
            await conn.execute('''
                INSERT INTO players 
                (discord_id, game_id, game_nickname, current_clan, page_info, tier, tier_assigned_at, tier_assigned_by, updated_at)
                SELECT $1, game_id, game_nickname, current_clan, page_info, $2, $3, $4, $5
                FROM applications WHERE discord_id = $1 
                ORDER BY created_at DESC LIMIT 1
                ON CONFLICT (discord_id) 
                DO UPDATE SET 
                    tier = $2,
                    tier_assigned_at = $3,
                    tier_assigned_by = $4,
                    updated_at = $5
            ''', discord_id, new_tier, current_time, assigned_by, current_time)

            # Log tier assignment
            await conn.execute('''
                INSERT INTO tier_assignments 
                (discord_id, old_tier, new_tier, assigned_by, assigned_at, application_id)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', discord_id, old_tier, new_tier, assigned_by, current_time, application_id)

    async def get_tier_leaderboard(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get tier leaderboard"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM players 
                WHERE tier != 'None'
                ORDER BY 
                    CASE tier 
                        WHEN 'T1' THEN 1 
                        WHEN 'T2' THEN 2 
                        WHEN 'T3' THEN 3 
                        WHEN 'T4' THEN 4 
                        WHEN 'T5' THEN 5 
                        ELSE 6 
                    END,
                    tier_assigned_at DESC
                LIMIT $1
            ''', limit)

            return [dict(row) for row in rows]

    async def get_player_by_discord_id(self, discord_id: str) -> Optional[Dict[str, Any]]:
        """Get player by Discord ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT * FROM players WHERE discord_id = $1
            ''', discord_id)

            return dict(row) if row else None

    async def has_pending_application(self, discord_id: str) -> bool:
        """Check if user has pending application"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow('''
                SELECT id FROM applications 
                WHERE discord_id = $1 AND status = 'pending'
                LIMIT 1
            ''', discord_id)

            return result is not None

    async def set_guild_applications_channel(self, guild_id: str, channel_id: str):
        """Set applications channel for guild"""
        async with self.pool.acquire() as conn:
            current_time = int(datetime.now().timestamp())

            await conn.execute('''
                INSERT INTO guild_settings (guild_id, applications_channel_id, created_at, updated_at)
                VALUES ($1, $2, $3, $3)
                ON CONFLICT (guild_id) 
                DO UPDATE SET 
                    applications_channel_id = $2,
                    updated_at = $3
            ''', guild_id, channel_id, current_time)

    async def get_guild_applications_channel(self, guild_id: str) -> Optional[str]:
        """Get applications channel for guild"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT applications_channel_id FROM guild_settings WHERE guild_id = $1
            ''', guild_id)

            return row['applications_channel_id'] if row else None

    async def set_guild_tierlist_channel(self, guild_id: str, channel_id: str, message_id: str = None):
        """Set tierlist channel and message for guild"""
        async with self.pool.acquire() as conn:
            current_time = int(datetime.now().timestamp())

            await conn.execute('''
                INSERT INTO guild_settings 
                (guild_id, tier_list_channel_id, tier_list_message_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $4)
                ON CONFLICT (guild_id) 
                DO UPDATE SET 
                    tier_list_channel_id = $2,
                    tier_list_message_id = $3,
                    updated_at = $4
            ''', guild_id, channel_id, message_id, current_time)

    async def get_guild_tierlist_info(self, guild_id: str) -> Optional[Dict[str, str]]:
        """Get tierlist channel and message info for guild"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT tier_list_channel_id, tier_list_message_id 
                FROM guild_settings WHERE guild_id = $1
            ''', guild_id)

            if row:
                return {
                    'channel_id': row['tier_list_channel_id'],
                    'message_id': row['tier_list_message_id']
                }
            return None

    async def set_guild_allowed_roles(self, guild_id: str, role_ids: List[str]):
        """Set roles that can use the bot"""
        role_ids_str = ','.join(role_ids) if role_ids else None
        async with self.pool.acquire() as conn:
            current_time = int(datetime.now().timestamp())

            await conn.execute('''
                INSERT INTO guild_settings (guild_id, allowed_roles, created_at, updated_at)
                VALUES ($1, $2, $3, $3)
                ON CONFLICT (guild_id) 
                DO UPDATE SET 
                    allowed_roles = $2,
                    updated_at = $3
            ''', guild_id, role_ids_str, current_time)

    async def set_guild_admin_roles(self, guild_id: str, role_ids: List[str]):
        """Set roles that can assign tiers"""
        role_ids_str = ','.join(role_ids) if role_ids else None
        async with self.pool.acquire() as conn:
            current_time = int(datetime.now().timestamp())

            await conn.execute('''
                INSERT INTO guild_settings (guild_id, admin_roles, created_at, updated_at)
                VALUES ($1, $2, $3, $3)
                ON CONFLICT (guild_id) 
                DO UPDATE SET 
                    admin_roles = $2,
                    updated_at = $3
            ''', guild_id, role_ids_str, current_time)

    async def get_guild_allowed_roles(self, guild_id: str) -> List[str]:
        """Get roles that can use the bot"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT allowed_roles FROM guild_settings WHERE guild_id = $1
            ''', guild_id)

            if row and row['allowed_roles']:
                return row['allowed_roles'].split(',')
            return []

    async def get_guild_admin_roles(self, guild_id: str) -> List[str]:
        """Get roles that can assign tiers"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT admin_roles FROM guild_settings WHERE guild_id = $1
            ''', guild_id)

            if row and row['admin_roles']:
                return row['admin_roles'].split(',')
            return []

    async def save_persistent_view(self, message_id: str, channel_id: str, guild_id: str, 
                                 view_type: str, view_data: dict = None):
        """Save persistent view data"""
        async with self.pool.acquire() as conn:
            current_time = int(datetime.now().timestamp())

            await conn.execute('''
                INSERT INTO persistent_views 
                (message_id, channel_id, guild_id, view_type, view_data, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (message_id) 
                DO UPDATE SET 
                    view_data = $5
            ''', message_id, channel_id, guild_id, view_type, view_data, current_time)

    async def get_persistent_views(self) -> List[Dict[str, Any]]:
        """Get all persistent views for restoration"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM persistent_views ORDER BY created_at DESC
            ''')

            return [dict(row) for row in rows]

    async def delete_persistent_view(self, message_id: str):
        """Delete persistent view"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                DELETE FROM persistent_views WHERE message_id = $1
            ''', message_id)