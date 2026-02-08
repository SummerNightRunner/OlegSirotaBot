import discord
from discord import ui, Interaction

from src.db.onboarding_store import OnboardingStore
from src.utils.logs import debug, info, warn


class EnterHouseView(ui.View):
    def __init__(self, cfg, store: OnboardingStore):
        super().__init__(timeout=None)
        self.cfg = cfg
        self.store = store

    @ui.button(
        label="Выйти из детской",
        style=discord.ButtonStyle.success,
        custom_id="enter_house_button",
    )
    async def enter_house(self, interaction: Interaction, button: ui.Button):
        guild = interaction.guild
        member = interaction.user

        if guild is None:
            debug("ENTER_HOUSE", "guild_is_none")
            return

        # 0) персональная защита
        message = interaction.message
        if message is None:
            warn("ENTER_HOUSE", "interaction_without_message")
            await interaction.response.send_message(
                "Сын, эта кнопка без письма. Попроси новую.",
                ephemeral=True,
            )
            return
        owner_id = await self.store.get_user_by_message(guild.id, message.id)
        if owner_id is None:
            warn("ENTER_HOUSE", "owner_missing_for_message", guild=guild.id, msg=message.id)
            await interaction.response.send_message(
                "Сын, это письмо потерялось. Попроси новое приглашение.",
                ephemeral=True,
            )
            return
        if owner_id != interaction.user.id:
            warn(
                "ENTER_HOUSE",
                "wrong_user",
                guild=guild.id,
                msg=message.id,
                owner=owner_id,
                actor=interaction.user.id,
            )
            await interaction.response.send_message(
                "Эта кнопка не для тебя, сынок.",
                ephemeral=True,
            )
            return

        newborn = guild.get_role(self.cfg.role_newborn_id)
        member_role = guild.get_role(self.cfg.role_member_id)

        # 1) защита: кнопка только для новорождённых
        if newborn is None or newborn not in member.roles:
            warn("ENTER_HOUSE", "not_newborn", guild=guild.id, user=member.id)
            await interaction.response.send_message(
                "Тебе не сюда.",
                ephemeral=True,
            )
            return

        # 2) проверка: написал ли первые слова
        has = await self.store.has_first_words(guild.id, member.id)
        if not has:
            info("ENTER_HOUSE", "no_first_words", guild=guild.id, user=member.id)
            await interaction.response.send_message(
                "Напиши здесь свои первые слова, сынок, нажми кнопку ниже и тогда ты сможешь выйти к своим братьям.",
                ephemeral=True,
            )
            return

        # 3) меняем роли
        await member.remove_roles(newborn, reason="Onboarding")
        if member_role:
            await member.add_roles(member_role, reason="Onboarding")

        # 4) журнал
        journal = guild.get_channel(self.cfg.channel_journal_id)
        if isinstance(journal, discord.TextChannel):
            await journal.send(f"{member.mention} вышел из детской.")

        await interaction.response.send_message(
            "Добро пожаловать в дом, сын.",
            ephemeral=True,
        )

        # 5) очистка
        info("ENTER_HOUSE", "success", guild=guild.id, user=member.id)
        await self.store.delete_onboarding_state(guild.id, member.id)
