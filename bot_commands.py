import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from views_persistent import PersistentTierApplicationView
from models import get_tier_emoji
from config import Config

class TierCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def check_user_permissions(self, interaction: discord.Interaction, need_admin: bool = False) -> bool:
        """Check if user has permissions to use bot commands"""
        # Server owner and administrators always have access
        if interaction.user.guild_permissions.administrator:
            return True
        
        guild_id = str(interaction.guild.id)
        
        if need_admin:
            # Check admin roles for tier assignment
            admin_roles = await self.bot.db.get_guild_admin_roles(guild_id)
            if admin_roles:
                user_role_ids = [str(role.id) for role in interaction.user.roles]
                return any(role_id in admin_roles for role_id in user_role_ids)
            return False
        else:
            # Check allowed roles for general bot usage
            allowed_roles = await self.bot.db.get_guild_allowed_roles(guild_id)
            if not allowed_roles:
                # If no roles set, allow everyone
                return True
            
            user_role_ids = [str(role.id) for role in interaction.user.roles]
            return any(role_id in allowed_roles for role_id in user_role_ids)
    
    @app_commands.command(name="tier_button", description="Отправить кнопку для подачи заявки на тир")
    @app_commands.describe(channel="Канал для отправки кнопки (по умолчанию текущий)")
    async def tier_button(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        """Send tier application button"""
        # Check permissions
        if not await self.check_user_permissions(interaction, need_admin=True):
            await interaction.response.send_message(
                "❌ У вас нет прав для использования этой команды!",
                ephemeral=True
            )
            return
        
        target_channel = channel or interaction.channel
        
        # Create embed
        embed = discord.Embed(
            title="🎯 Система тиров",
            description=(
                "Подайте заявку на получение тира!\n\n"
                "**Доступные тиры:**\n"
                f"{get_tier_emoji('T1')} **T1** - Высший тир\n"
                f"{get_tier_emoji('T2')} **T2** - Второй тир\n"
                f"{get_tier_emoji('T3')} **T3** - Третий тир\n"
                f"{get_tier_emoji('T4')} **T4** - Четвертый тир\n"
                f"{get_tier_emoji('T5')} **T5** - Пятый тир\n\n"
                "Нажмите кнопку ниже, чтобы подать заявку!"
            ),
            color=Config.COLOR_INFO
        )
        
        embed.set_footer(text="Заполните все поля в форме для подачи заявки")
        
        # Create persistent view with button
        view = PersistentTierApplicationView()
        
        # Send message
        message = await target_channel.send(embed=embed, view=view)
        
        # Save persistent view
        await self.bot.db.save_persistent_view(
            message_id=str(message.id),
            channel_id=str(target_channel.id),
            guild_id=str(interaction.guild.id),
            view_type="tier_application"
        )
        
        await interaction.response.send_message(
            f"✅ Кнопка для подачи заявки отправлена в {target_channel.mention}",
            ephemeral=True
        )
    
    @app_commands.command(name="tier_top", description="Показать топ игроков по тирам")
    @app_commands.describe(limit="Количество игроков для отображения (по умолчанию 20)")
    async def tier_top(self, interaction: discord.Interaction, limit: Optional[int] = 20):
        """Show tier leaderboard"""
        if limit < 1 or limit > 100:
            await interaction.response.send_message(
                "❌ Лимит должен быть от 1 до 100!",
                ephemeral=True
            )
            return
        
        # Get leaderboard
        leaderboard = await self.bot.db.get_tier_leaderboard(limit)
        
        if not leaderboard:
            await interaction.response.send_message(
                "📊 Пока нет игроков с присвоенными тирами.",
                ephemeral=True
            )
            return
        
        # Create embed
        embed = discord.Embed(
            title="🏆 Топ игроков по тирам",
            description="Рейтинг игроков по тирам (T1 - высший)",
            color=Config.COLOR_INFO
        )
        
        # Group by tiers
        tiers_data = {}
        for player in leaderboard:
            tier = player['tier']
            if tier not in tiers_data:
                tiers_data[tier] = []
            tiers_data[tier].append(player)
        
        # Add fields for each tier
        for tier in ['T1', 'T2', 'T3', 'T4', 'T5']:
            if tier in tiers_data:
                players = tiers_data[tier]
                players_list = []
                
                for i, player in enumerate(players, 1):
                    try:
                        user = self.bot.get_user(int(player['discord_id']))
                        username = user.display_name if user else f"ID: {player['discord_id']}"
                        game_nick = player.get('game_nickname', 'N/A')
                        players_list.append(f"{i}. {username} ({game_nick})")
                    except:
                        players_list.append(f"{i}. ID: {player['discord_id']}")
                
                if players_list:
                    embed.add_field(
                        name=f"{get_tier_emoji(tier)} {tier} ({len(players)} игроков)",
                        value="\n".join(players_list[:10]),  # Limit to 10 per tier
                        inline=False
                    )
        
        embed.set_footer(text=f"Показано {len(leaderboard)} игроков из {limit} запрошенных")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="set_applications_channel", description="Установить канал для заявок")
    @app_commands.describe(channel="Канал для отправки заявок")
    async def set_applications_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set applications channel"""
        # Check permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ У вас нет прав для использования этой команды!",
                ephemeral=True
            )
            return
        
        # Set channel
        await self.bot.db.set_guild_applications_channel(
            guild_id=str(interaction.guild.id),
            channel_id=str(channel.id)
        )
        
        await interaction.response.send_message(
            f"✅ Канал для заявок установлен: {channel.mention}",
            ephemeral=True
        )
    
    @app_commands.command(name="my_tier", description="Показать ваш текущий тир")
    async def my_tier(self, interaction: discord.Interaction):
        """Show user's current tier"""
        # Check permissions
        if not await self.check_user_permissions(interaction, need_admin=False):
            await interaction.response.send_message(
                "❌ У вас нет прав для использования этой команды!",
                ephemeral=True
            )
            return
        
        player = await self.bot.db.get_player_by_discord_id(str(interaction.user.id))
        
        if not player or player['tier'] == 'None':
            await interaction.response.send_message(
                "❌ У вас пока нет присвоенного тира. Подайте заявку!",
                ephemeral=True
            )
            return
        
        tier = player['tier']
        embed = discord.Embed(
            title="🎯 Ваш тир",
            description=f"Ваш текущий тир: **{tier}** {get_tier_emoji(tier)}",
            color=Config.get_tier_color(tier)
        )
        
        if player['tier_assigned_at']:
            embed.add_field(
                name="📅 Присвоен",
                value=f"<t:{int(player['tier_assigned_at'])}:R>",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="player_info", description="Показать информацию об игроке")
    @app_commands.describe(user="Пользователь для просмотра информации")
    async def player_info(self, interaction: discord.Interaction, user: discord.Member):
        """Show player information"""
        player = await self.bot.db.get_player_by_discord_id(str(user.id))
        
        if not player:
            await interaction.response.send_message(
                f"❌ Информация об игроке {user.mention} не найдена.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"👤 Информация об игроке",
            description=f"**Пользователь:** {user.mention}",
            color=Config.get_tier_color(player['tier']) if player['tier'] != 'None' else Config.COLOR_INFO
        )
        
        embed.add_field(
            name="🎯 Тир",
            value=f"{get_tier_emoji(player['tier'])} {player['tier']}" if player['tier'] != 'None' else "Не присвоен",
            inline=True
        )
        
        if player.get('game_nickname'):
            embed.add_field(
                name="🎮 Ник в игре",
                value=player['game_nickname'],
                inline=True
            )
        
        if player.get('tier_assigned_at'):
            embed.add_field(
                name="📅 Тир присвоен",
                value=f"<t:{int(player['tier_assigned_at'])}:R>",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="remove_tier", description="Снять тир с игрока")
    @app_commands.describe(user="Пользователь для снятия тира")
    async def remove_tier(self, interaction: discord.Interaction, user: discord.Member):
        """Remove tier from player"""
        # Check permissions
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "❌ У вас нет прав для использования этой команды!",
                ephemeral=True
            )
            return
        
        player = await self.bot.db.get_player_by_discord_id(str(user.id))
        
        if not player or player['tier'] == 'None':
            await interaction.response.send_message(
                f"❌ У пользователя {user.mention} нет присвоенного тира.",
                ephemeral=True
            )
            return
        
        # Remove tier
        await self.bot.db.assign_tier(
            discord_id=str(user.id),
            new_tier='None',
            assigned_by=str(interaction.user.id)
        )
        
        # Update tier list
        try:
            await self.update_tierlist(str(interaction.guild.id))
        except Exception as e:
            print(f"Error updating tierlist: {e}")
        
        await interaction.response.send_message(
            f"✅ Тир снят с пользователя {user.mention}",
            ephemeral=True
        )
        
        # Notify user
        try:
            await user.send(
                f"📢 Ваш тир был снят администратором {interaction.user.mention}."
            )
        except:
            pass  # User might have DMs disabled
    
    @app_commands.command(name="setup_tierlist", description="Создать автоматически обновляемый тир-лист")
    @app_commands.describe(channel="Канал для тир-листа")
    async def setup_tierlist(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        """Setup auto-updating tier list"""
        # Check permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ У вас нет прав для использования этой команды!",
                ephemeral=True
            )
            return
        
        target_channel = channel or interaction.channel
        
        # Create tier list embed
        embed = await self.create_tierlist_embed()
        
        # Send tier list message
        message = await target_channel.send(embed=embed)
        
        # Save tier list info
        await self.bot.db.set_guild_tierlist_channel(
            guild_id=str(interaction.guild.id),
            channel_id=str(target_channel.id),
            message_id=str(message.id)
        )
        
        await interaction.response.send_message(
            f"✅ Тир-лист создан в {target_channel.mention}! Он будет автоматически обновляться при выдаче тиров.",
            ephemeral=True
        )
    
    async def create_tierlist_embed(self):
        """Create tier list embed"""
        # Get leaderboard
        leaderboard = await self.bot.db.get_tier_leaderboard(100)
        
        embed = discord.Embed(
            title="🏆 Тиры игроков",
            description="Список игроков по тирам",
            color=Config.COLOR_INFO
        )
        
        # Group by tiers
        tiers_data = {}
        for player in leaderboard:
            tier = player['tier']
            if tier not in tiers_data:
                tiers_data[tier] = []
            tiers_data[tier].append(player)
        
        # Add fields for each tier
        for tier in ['T1', 'T2', 'T3', 'T4', 'T5']:
            if tier in tiers_data:
                players = tiers_data[tier]
                players_list = []
                
                for player in players:
                    try:
                        user = self.bot.get_user(int(player['discord_id']))
                        username = user.display_name if user else f"ID: {player['discord_id']}"
                        game_nick = player.get('game_nickname', 'N/A')
                        if game_nick and game_nick != 'N/A':
                            players_list.append(f"• {game_nick}")
                        else:
                            players_list.append(f"• {username}")
                    except:
                        players_list.append(f"• ID: {player['discord_id']}")
                
                if players_list:
                    embed.add_field(
                        name=f"{get_tier_emoji(tier)} {tier}",
                        value="\n".join(players_list[:15]) + (f"\n... и еще {len(players_list) - 15}" if len(players_list) > 15 else ""),
                        inline=True
                    )
            else:
                embed.add_field(
                    name=f"{get_tier_emoji(tier)} {tier}",
                    value="Пусто",
                    inline=True
                )
        
        embed.set_footer(text=f"Автоматически обновляется при выдаче тиров • Всего игроков: {len(leaderboard)}")
        embed.timestamp = discord.utils.utcnow()
        
        return embed
    
    async def update_tierlist(self, guild_id: str):
        """Update tier list message"""
        try:
            tierlist_info = await self.bot.db.get_guild_tierlist_info(guild_id)
            if not tierlist_info or not tierlist_info.get('channel_id') or not tierlist_info.get('message_id'):
                return
            
            channel = self.bot.get_channel(int(tierlist_info['channel_id']))
            if not channel:
                return
            
            try:
                message = await channel.fetch_message(int(tierlist_info['message_id']))
                embed = await self.create_tierlist_embed()
                await message.edit(embed=embed)
            except discord.NotFound:
                # Message was deleted, create new one
                embed = await self.create_tierlist_embed()
                new_message = await channel.send(embed=embed)
                await self.bot.db.set_guild_tierlist_channel(
                    guild_id=guild_id,
                    channel_id=str(channel.id),
                    message_id=str(new_message.id)
                )
        except Exception as e:
            print(f"Error updating tierlist: {e}")
    
    @app_commands.command(name="setup_roles", description="Настроить роли для использования бота")
    @app_commands.describe(
        allowed_roles="Роли, которые могут использовать бота (через пробел)",
        admin_roles="Роли, которые могут выдавать тиры (через пробел)"
    )
    async def setup_roles(self, interaction: discord.Interaction, allowed_roles: str = "", admin_roles: str = ""):
        """Setup roles for bot usage"""
        # Check permissions - only administrators can set up roles
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ У вас нет прав для использования этой команды!",
                ephemeral=True
            )
            return
        
        guild_id = str(interaction.guild.id)
        
        # Parse roles
        allowed_role_ids = []
        admin_role_ids = []
        
        if allowed_roles.strip():
            # Parse allowed roles
            role_mentions = allowed_roles.split()
            for role_mention in role_mentions:
                role_id = role_mention.strip('<@&>')
                if role_id.isdigit():
                    role = interaction.guild.get_role(int(role_id))
                    if role:
                        allowed_role_ids.append(role_id)
        
        if admin_roles.strip():
            # Parse admin roles
            role_mentions = admin_roles.split()
            for role_mention in role_mentions:
                role_id = role_mention.strip('<@&>')
                if role_id.isdigit():
                    role = interaction.guild.get_role(int(role_id))
                    if role:
                        admin_role_ids.append(role_id)
        
        # Save to database
        if allowed_role_ids:
            await self.bot.db.set_guild_allowed_roles(guild_id, allowed_role_ids)
        if admin_role_ids:
            await self.bot.db.set_guild_admin_roles(guild_id, admin_role_ids)
        
        # Create response
        embed = discord.Embed(
            title="🛡️ Настройка ролей",
            description="Роли для бота настроены!",
            color=Config.COLOR_SUCCESS
        )
        
        if allowed_role_ids:
            allowed_roles_text = []
            for role_id in allowed_role_ids:
                role = interaction.guild.get_role(int(role_id))
                if role:
                    allowed_roles_text.append(f"• {role.name}")
            
            if allowed_roles_text:
                embed.add_field(
                    name="Роли для использования бота:",
                    value="\n".join(allowed_roles_text),
                    inline=False
                )
        else:
            embed.add_field(
                name="Роли для использования бота:",
                value="Все пользователи",
                inline=False
            )
        
        if admin_role_ids:
            admin_roles_text = []
            for role_id in admin_role_ids:
                role = interaction.guild.get_role(int(role_id))
                if role:
                    admin_roles_text.append(f"• {role.name}")
            
            if admin_roles_text:
                embed.add_field(
                    name="Роли для выдачи тиров:",
                    value="\n".join(admin_roles_text),
                    inline=False
                )
        else:
            embed.add_field(
                name="Роли для выдачи тиров:",
                value="Только администраторы",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="roles_info", description="Показать текущие настройки ролей")
    async def roles_info(self, interaction: discord.Interaction):
        """Show current role settings"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ У вас нет прав для использования этой команды!",
                ephemeral=True
            )
            return
        
        guild_id = str(interaction.guild.id)
        
        # Get current roles
        allowed_roles = await self.bot.db.get_guild_allowed_roles(guild_id)
        admin_roles = await self.bot.db.get_guild_admin_roles(guild_id)
        
        embed = discord.Embed(
            title="🛡️ Настройки ролей",
            description="Текущие настройки доступа к боту",
            color=Config.COLOR_INFO
        )
        
        # Allowed roles
        if allowed_roles:
            allowed_roles_text = []
            for role_id in allowed_roles:
                role = interaction.guild.get_role(int(role_id))
                if role:
                    allowed_roles_text.append(f"• {role.name}")
            
            if allowed_roles_text:
                embed.add_field(
                    name="Роли для использования бота:",
                    value="\n".join(allowed_roles_text),
                    inline=False
                )
        else:
            embed.add_field(
                name="Роли для использования бота:",
                value="Все пользователи",
                inline=False
            )
        
        # Admin roles
        if admin_roles:
            admin_roles_text = []
            for role_id in admin_roles:
                role = interaction.guild.get_role(int(role_id))
                if role:
                    admin_roles_text.append(f"• {role.name}")
            
            if admin_roles_text:
                embed.add_field(
                    name="Роли для выдачи тиров:",
                    value="\n".join(admin_roles_text),
                    inline=False
                )
        else:
            embed.add_field(
                name="Роли для выдачи тиров:",
                value="Только администраторы",
                inline=False
            )
        
        embed.add_field(
            name="Как настроить:",
            value="Используйте `/setup_roles` для настройки ролей",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TierCommands(bot))
