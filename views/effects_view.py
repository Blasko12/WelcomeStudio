import discord
from discord.ext import commands


class EditorEfectosView(discord.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        guild: discord.Guild,
        usuario: discord.Member,
    ) -> None:
        super().__init__(timeout=300)

        self.bot = bot
        self.guild = guild
        self.usuario = usuario

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.user.id != self.usuario.id:
            await interaction.response.send_message(
                "❌ Solo la persona que abrió el editor puede usarlo.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="Volver",
        emoji="↩️",
        style=discord.ButtonStyle.success,
    )
    async def volver(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        from views.editor_view import (
            EditorPrincipalView,
            generar_archivo_editor,
        )

        vista = EditorPrincipalView(
            bot=self.bot,
            guild=self.guild,
            usuario=self.usuario,
        )

        archivo = await generar_archivo_editor(
            self.guild,
            self.usuario,
        )

        await interaction.response.edit_message(
            content=vista.texto_principal(),
            attachments=[archivo],
            view=vista,
        )