import discord
from discord.ext import commands
from typing import Optional
from models import get_tier_emoji
from config import Config

class TierApplicationModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Заявка на тир")
        
        self.game_id = discord.ui.TextInput(
            label="ID в игре",
            placeholder="Введите ваш ID в игре",
            required=True,
            max_length=100
        )
        
        self.game_nickname = discord.ui.TextInput(
            label="Ник в игре",
            placeholder="Введите ваш ник в игре",
            required=True,
            max_length=100
        )
        
        self.current_clan = discord.ui.TextInput(
            label="Текущий клан",
            placeholder="Введите название вашего клана",
            required=False,
            max_length=100
        )
        
        self.page_info = discord.ui.TextInput(
            label="Пейдж",
            placeholder="Введите информацию о пейдже",
            required=False,
            max_length=200
        )
        
        self.desired_tier = discord.ui.TextInput(
            label="Желаемый тир (T1-T5)",
            placeholder="T1, T2, T3, T4 или T5",
            required=True,
            max_length=2
        )
        
        self.add_item(self.game_id)
        self.add_item(self.game_nickname)
        self.add_item(self.current_clan)
        self.add_item(self.page_info)
        self.add_item(self.desired_tier)
    
    async def on_submit(self, interaction: discord.Interaction):
        # Validate tier
        desired_tier = self.desired_tier.value.upper()
        if desired_tier not in Config.AVAILABLE_TIERS:
            await interaction.response.send_message(
                f"❌ Неверный тир! Доступные тиры: {', '.join(Config.AVAILABLE_TIERS)}", 
                ephemeral=True
            )
            return
        
        # Check if user has pending application
        bot = interaction.client
        has_pending = await bot.db.has_pending_application(str(interaction.user.id))
        
        if has_pending:
            await interaction.response.send_message(
                "❌ Ваша активная заявка еще не рассмотрена! Дождитесь решения администратора, после чего сможете подать новую заявку.",
                ephemeral=True
            )
            return
        
        # Create application
        try:
            app_id = await bot.db.create_application(
                discord_id=str(interaction.user.id),
                game_id=self.game_id.value,
                game_nickname=self.game_nickname.value,
                current_clan=self.current_clan.value or "Не указан",
                page_info=self.page_info.value or "Не указан",
                desired_tier=desired_tier
            )
            
            # Get applications channel
            channel_id = await bot.db.get_guild_applications_channel(str(interaction.guild.id))
            
            if not channel_id:
                await interaction.response.send_message(
                    "❌ Канал для заявок не настроен! Обратитесь к администратору.",
                    ephemeral=True
                )
                return
            
            channel = bot.get_channel(int(channel_id))
            if not channel:
                await interaction.response.send_message(
                    "❌ Канал для заявок не найден! Обратитесь к администратору.",
                    ephemeral=True
                )
                return
            
            # Create embed for application
            embed = discord.Embed(
                title=f"📋 Заявка на тир {desired_tier}",
                color=Config.get_tier_color(desired_tier),
                timestamp=interaction.created_at
            )
            
            embed.add_field(name="👤 Пользователь", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="🎮 ID в игре", value=self.game_id.value, inline=True)
            embed.add_field(name="🏷️ Ник в игре", value=self.game_nickname.value, inline=True)
            embed.add_field(name="🏰 Клан", value=self.current_clan.value or "Не указан", inline=True)
            embed.add_field(name="📄 Пейдж", value=self.page_info.value or "Не указан", inline=True)
            embed.add_field(name="🎯 Желаемый тир", value=f"{get_tier_emoji(desired_tier)} {desired_tier}", inline=True)
            
            embed.set_footer(text=f"ID заявки: {app_id}")
            
            # Create tier assignment view
            view = TierAssignmentView(app_id)
            
            # Send to applications channel
            message = await channel.send(embed=embed, view=view)
            
            await interaction.response.send_message(
                f"✅ Ваша заявка на тир {desired_tier} успешно отправлена! Ожидайте рассмотрения.",
                ephemeral=True
            )
            
        except Exception as e:
            print(f"Error creating application: {e}")
            await interaction.response.send_message(
                "❌ Произошла ошибка при создании заявки. Попробуйте еще раз.",
                ephemeral=True
            )

class TierApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label="Подать заявку на тир",
        style=discord.ButtonStyle.primary,
        emoji="📋"
    )
    async def submit_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check user permissions
        guild_id = str(interaction.guild.id)
        bot = interaction.client
        
        # Get allowed roles
        allowed_roles = await bot.db.get_guild_allowed_roles(guild_id)
        
        if allowed_roles:
            # Check if user has required role
            user_role_ids = [str(role.id) for role in interaction.user.roles]
            has_permission = any(role_id in allowed_roles for role_id in user_role_ids)
            
            if not has_permission and not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ У вас нет прав для подачи заявки!",
                    ephemeral=True
                )
                return
        
        # Check if user already has pending application
        has_pending = await bot.db.has_pending_application(str(interaction.user.id))
        
        if has_pending:
            await interaction.response.send_message(
                "❌ У вас уже есть активная заявка! Дождитесь рассмотрения.",
                ephemeral=True
            )
            return
        
        modal = TierApplicationModal()
        await interaction.response.send_modal(modal)

class TierAssignmentView(discord.ui.View):
    def __init__(self, application_id: int):
        super().__init__(timeout=None)
        self.application_id = application_id
    
    @discord.ui.button(label="T1", style=discord.ButtonStyle.success, emoji="🏆")
    async def assign_t1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_tier(interaction, "T1")
    
    @discord.ui.button(label="T2", style=discord.ButtonStyle.secondary, emoji="🥈")
    async def assign_t2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_tier(interaction, "T2")
    
    @discord.ui.button(label="T3", style=discord.ButtonStyle.secondary, emoji="🥉")
    async def assign_t3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_tier(interaction, "T3")
    
    @discord.ui.button(label="T4", style=discord.ButtonStyle.secondary, emoji="🎖️")
    async def assign_t4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_tier(interaction, "T4")
    
    @discord.ui.button(label="T5", style=discord.ButtonStyle.secondary, emoji="🏅")
    async def assign_t5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_tier(interaction, "T5")
    
    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger, emoji="❌")
    async def reject_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.reject_application_handler(interaction)
    
    async def assign_tier(self, interaction: discord.Interaction, tier: str):
        """Assign tier to user"""
        # Check admin permissions
        guild_id = str(interaction.guild.id)
        bot = interaction.client
        
        # Get admin roles
        admin_roles = await bot.db.get_guild_admin_roles(guild_id)
        
        if admin_roles:
            # Check if user has admin role
            user_role_ids = [str(role.id) for role in interaction.user.roles]
            has_admin_permission = any(role_id in admin_roles for role_id in user_role_ids)
            
            if not has_admin_permission and not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ У вас нет прав для выдачи тиров!",
                    ephemeral=True
                )
                return
        elif not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ У вас нет прав для выдачи тиров!",
                ephemeral=True
            )
            return
        
        try:
            bot = interaction.client
            
            # Get application
            app = await bot.db.get_application(self.application_id)
            if not app:
                await interaction.response.send_message(
                    "❌ Заявка не найдена!",
                    ephemeral=True
                )
                return
            
            if app['status'] != 'pending':
                await interaction.response.send_message(
                    "❌ Эта заявка уже была обработана!",
                    ephemeral=True
                )
                return
            
            # Assign tier
            await bot.db.assign_tier(
                discord_id=app['discord_id'],
                new_tier=tier,
                assigned_by=str(interaction.user.id),
                application_id=self.application_id
            )
            
            # Update application status
            await bot.db.update_application_status(
                app_id=self.application_id,
                status='approved',
                processed_by=str(interaction.user.id)
            )
            
            # Update embed
            embed = interaction.message.embeds[0]
            embed.color = Config.get_tier_color(tier)
            embed.title = f"✅ Заявка одобрена - Тир {tier}"
            embed.add_field(
                name="👨‍💼 Обработано",
                value=f"{interaction.user.mention} - {tier}",
                inline=False
            )
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Update tier list
            try:
                tier_commands = bot.get_cog('TierCommands')
                if tier_commands:
                    await tier_commands.update_tierlist(str(interaction.guild.id))
            except Exception as e:
                print(f"Error updating tierlist: {e}")
            
            # Notify user
            try:
                user = bot.get_user(int(app['discord_id']))
                if user:
                    await user.send(
                        f"🎉 Ваша заявка на тир одобрена! Вам присвоен тир **{tier}** {get_tier_emoji(tier)}\n\n"
                        f"Теперь вы можете подать новую заявку для изменения тира, если потребуется."
                    )
            except:
                pass  # User might have DMs disabled
            
        except Exception as e:
            print(f"Error assigning tier: {e}")
            await interaction.response.send_message(
                "❌ Произошла ошибка при выдаче тира.",
                ephemeral=True
            )
    
    async def reject_application_handler(self, interaction: discord.Interaction):
        """Reject application"""
        # Check admin permissions
        guild_id = str(interaction.guild.id)
        bot = interaction.client
        
        # Get admin roles
        admin_roles = await bot.db.get_guild_admin_roles(guild_id)
        
        if admin_roles:
            # Check if user has admin role
            user_role_ids = [str(role.id) for role in interaction.user.roles]
            has_admin_permission = any(role_id in admin_roles for role_id in user_role_ids)
            
            if not has_admin_permission and not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ У вас нет прав для отклонения заявок!",
                    ephemeral=True
                )
                return
        elif not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ У вас нет прав для отклонения заявок!",
                ephemeral=True
            )
            return
        
        try:
            bot = interaction.client
            
            # Get application
            app = await bot.db.get_application(self.application_id)
            if not app:
                await interaction.response.send_message(
                    "❌ Заявка не найдена!",
                    ephemeral=True
                )
                return
            
            if app['status'] != 'pending':
                await interaction.response.send_message(
                    "❌ Эта заявка уже была обработана!",
                    ephemeral=True
                )
                return
            
            # Update application status
            await bot.db.update_application_status(
                app_id=self.application_id,
                status='rejected',
                processed_by=str(interaction.user.id)
            )
            
            # Update embed
            embed = interaction.message.embeds[0]
            embed.color = Config.COLOR_ERROR
            embed.title = "❌ Заявка отклонена"
            embed.add_field(
                name="👨‍💼 Обработано",
                value=f"{interaction.user.mention} - Отклонена",
                inline=False
            )
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Notify user
            try:
                user = bot.get_user(int(app['discord_id']))
                if user:
                    await user.send(
                        "❌ Ваша заявка на тир была отклонена.\n\n"
                        "Вы можете подать новую заявку с исправленными данными."
                    )
            except:
                pass  # User might have DMs disabled
            
        except Exception as e:
            print(f"Error rejecting application: {e}")
            await interaction.response.send_message(
                "❌ Произошла ошибка при отклонении заявки.",
                ephemeral=True
            )
