import os

class Config:
    # Bot settings
    COMMAND_PREFIX = '!'
    
    # Tier settings
    AVAILABLE_TIERS = ['T1', 'T2', 'T3', 'T4', 'T5']
    
    # Application settings
    MAX_PENDING_APPLICATIONS = 1  # Max pending applications per user
    
    # Colors
    COLOR_SUCCESS = 0x00ff00
    COLOR_ERROR = 0xff0000
    COLOR_WARNING = 0xffff00
    COLOR_INFO = 0x0099ff
    COLOR_TIER_T1 = 0xffd700  # Gold
    COLOR_TIER_T2 = 0xc0c0c0  # Silver
    COLOR_TIER_T3 = 0xcd7f32  # Bronze
    COLOR_TIER_T4 = 0x4169e1  # Royal Blue
    COLOR_TIER_T5 = 0x32cd32  # Lime Green
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'tier_bot.db')
    
    # Discord
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    
    @staticmethod
    def get_tier_color(tier: str) -> int:
        """Get color for tier"""
        colors = {
            'T1': Config.COLOR_TIER_T1,
            'T2': Config.COLOR_TIER_T2,
            'T3': Config.COLOR_TIER_T3,
            'T4': Config.COLOR_TIER_T4,
            'T5': Config.COLOR_TIER_T5
        }
        return colors.get(tier, Config.COLOR_INFO)
