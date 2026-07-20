import discord
from discord.ext import commands

from utils.config_manager import (
    actualizar_configuracion_servidor,
    obtener_configuracion_servidor,
)
from views.editor_view import generar_archivo_editor


class EditorAvatarView(discord.ui.View):
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

    def texto_estado(self, datos: dict) -> str:
        return (
            "😀 **Editor del avatar**\n\n"
            f"Posición X: `{datos.get('avatar_x', 0)}`\n"
            f"Posición Y: `{datos.get('avatar_y', 0)}`\n"
            f"Tamaño: `{datos.get('avatar_size', 235)} px`\n\n"
            "Usa los botones para moverlo o cambiar su tamaño."
        )

    async def cambiar(
        self,
        interaction: discord.Interaction,
        mover_x: int = 0,
        mover_y: int = 0,
        cambiar_tamano: int = 0,
        restablecer: bool = False,
    ) -> None:
        datos = obtener_configuracion_servidor(
            self.guild.id
        )

        if restablecer:
            nuevo_x = 0
            nuevo_y = 0
            nuevo_tamano = 235
        else:
            nuevo_x = (
                int(datos.get("avatar_x", 0))
                + mover_x
            )

            nuevo_y = (
                int(datos.get("avatar_y", 0))
                + mover_y
            )

            nuevo_tamano = max(
                100,
                min(
                    450,
                    int(datos.get("avatar_size", 235))
                    + cambiar_tamano,
                ),
            )

        datos = actualizar_configuracion_servidor(
            self.guild.id,
            avatar_x=nuevo_x,
            avatar_y=nuevo_y,
            avatar_size=nuevo_tamano,
        )

        try:
            archivo = await generar_archivo_editor(
                self.guild,
                self.usuario,
            )

            await interaction.response.edit_message(
                content=self.texto_estado(datos),
                attachments=[archivo],
                view=self,
            )

        except Exception as error:
            await interaction.response.send_message(
                f"❌ No se pudo actualizar el avatar: `{error}`",
                ephemeral=True,
            )

    @discord.ui.button(
        emoji="⬆️",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def arriba(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.cambiar(interaction, mover_y=-30)

    @discord.ui.button(
        emoji="⬅️",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def izquierda(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.cambiar(interaction, mover_x=-30)

    @discord.ui.button(
        label="Restablecer",
        emoji="♻️",
        style=discord.ButtonStyle.danger,
        row=1,
    )
    async def restablecer(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.cambiar(
            interaction,
            restablecer=True,
        )

    @discord.ui.button(
        emoji="➡️",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def derecha(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.cambiar(interaction, mover_x=30)

    @discord.ui.button(
        emoji="⬇️",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def abajo(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.cambiar(interaction, mover_y=30)

    @discord.ui.button(
        label="Reducir",
        emoji="➖",
        style=discord.ButtonStyle.primary,
        row=3,
    )
    async def reducir(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.cambiar(
            interaction,
            cambiar_tamano=-20,
        )

    @discord.ui.button(
        label="Aumentar",
        emoji="➕",
        style=discord.ButtonStyle.primary,
        row=3,
    )
    async def aumentar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.cambiar(
            interaction,
            cambiar_tamano=20,
        )

    @discord.ui.button(
        label="Volver",
        emoji="↩️",
        style=discord.ButtonStyle.success,
        row=4,
    )
    async def volver(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        from views.editor_view import EditorPrincipalView

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