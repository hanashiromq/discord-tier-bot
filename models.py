from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Player:
    discord_id: str
    game_id: str
    game_nickname: str
    current_clan: str
    page_info: str
    tier: str = "None"
    tier_assigned_at: Optional[datetime] = None
    tier_assigned_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Application:
    discord_id: str
    game_id: str
    game_nickname: str
    current_clan: str
    page_info: str
    desired_tier: str
    status: str = "pending"
    message_id: Optional[str] = None
    channel_id: Optional[str] = None
    created_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None

@dataclass
class TierAssignment:
    discord_id: str
    old_tier: Optional[str]
    new_tier: str
    assigned_by: str
    assigned_at: Optional[datetime] = None
    application_id: Optional[int] = None

# Tier hierarchy (T1 is highest, T5 is lowest)
TIER_HIERARCHY = {
    'T1': 1,
    'T2': 2,
    'T3': 3,
    'T4': 4,
    'T5': 5
}

TIER_EMOJIS = {
    'T1': '🏆',
    'T2': '🥈',
    'T3': '🥉',
    'T4': '🎖️',
    'T5': '🏅'
}

def get_tier_emoji(tier: str) -> str:
    """Get emoji for tier"""
    return TIER_EMOJIS.get(tier, '❓')
