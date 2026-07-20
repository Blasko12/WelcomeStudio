import discord
from discord.ext import commands

from utils.config_manager import (
    actualizar_configuracion_servidor,
    obtener_configuracion_servidor,
)
from views.editor_view import generar_archivo_editor


class EditorFondoView(discord.ui.View):
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
            "🖼️ **Editor del fondo**\n\n"
            f"Posición X: `{datos.get('background_x', 0)}`\n"
            f"Posición Y: `{datos.get('background_y', 0)}`\n"
            f"Zoom: "
            f"`{float(datos.get('background_zoom', 1.0)):.2f}x`\n\n"
            "Usa las flechas para mover el fondo."
        )

    async def cambiar(
        self,
        interaction: discord.Interaction,
        mover_x: int = 0,
        mover_y: int = 0,
        zoom: float = 0.0,
        restablecer: bool = False,
    ) -> None:
        await interaction.response.defer()

        datos = obtener_configuracion_servidor(
            self.guild.id
        )

        if restablecer:
            nuevo_x = 0
            nuevo_y = 0
            nuevo_zoom = 1.0
        else:
            nuevo_x = (
                int(datos.get("background_x", 0))
                + mover_x
            )

            nuevo_y = (
                int(datos.get("background_y", 0))
                + mover_y
            )

            nuevo_zoom = round(
                max(
                    1.0,
                    min(
                        3.0,
                        float(
                            datos.get(
                                "background_zoom",
                                1.0,
                            )
                        )
                        + zoom,
                    ),
                ),
                2,
            )

        datos = actualizar_configuracion_servidor(
            self.guild.id,
            background_x=nuevo_x,
            background_y=nuevo_y,
            background_zoom=nuevo_zoom,
        )

        try:
            archivo = await generar_archivo_editor(
                self.guild,
                self.usuario,
            )

            await interaction.edit_original_response(
                content=self.texto_estado(datos),
                attachments=[archivo],
                view=self,
            )

        except Exception as error:
            print(f"Error editor fondo: {error}")

            await interaction.edit_original_response(
                content=(
                    "❌ No se pudo actualizar el fondo:\n"
                    f"`{error}`"
                ),
                attachments=[],
                view=self,
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
        await self.cambiar(
            interaction,
            mover_y=-40,
        )

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
        await self.cambiar(
            interaction,
            mover_x=-40,
        )

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
        await self.cambiar(
            interaction,
            mover_x=40,
        )

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
        await self.cambiar(
            interaction,
            mover_y=40,
        )

    @discord.ui.button(
        label="Alejar",
        emoji="➖",
        style=discord.ButtonStyle.primary,
        row=3,
    )
    async def alejar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.cambiar(
            interaction,
            zoom=-0.10,
        )

    @discord.ui.button(
        label="Acercar",
        emoji="➕",
        style=discord.ButtonStyle.primary,
        row=3,
    )
    async def acercar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.cambiar(
            interaction,
            zoom=0.10,
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

        await interaction.response.defer()

        vista = EditorPrincipalView(
            bot=self.bot,
            guild=self.guild,
            usuario=self.usuario,
        )

        try:
            archivo = await generar_archivo_editor(
                self.guild,
                self.usuario,
            )

            await interaction.edit_original_response(
                content=vista.texto_principal(),
                attachments=[archivo],
                view=vista,
            )

        except Exception as error:
            print(f"Error al volver al editor principal: {error}")

            await interaction.edit_original_response(
                content=(
                    "❌ No se pudo volver al editor principal:\n"
                    f"`{error}`"
                ),
                attachments=[],
                view=self,
            )

    async def on_timeout(self) -> None:
        for componente in self.children:
            componente.disabled = True