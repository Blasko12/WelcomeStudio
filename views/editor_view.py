from pathlib import Path

import discord
from discord.ext import commands

from image_generator import generar_bienvenida
from utils.config_manager import obtener_configuracion_servidor


CARPETA_PROYECTO = Path(__file__).resolve().parent.parent


async def generar_archivo_editor(
    guild: discord.Guild,
    usuario: discord.Member,
) -> discord.File:
    datos = obtener_configuracion_servidor(guild.id)

    ruta_relativa = datos.get("background_path")

    if not ruta_relativa:
        raise FileNotFoundError(
            "Primero debes subir una imagen con `/fondo`."
        )

    ruta_fondo = CARPETA_PROYECTO / ruta_relativa

    if not ruta_fondo.exists():
        raise FileNotFoundError(
            "No se encontró la imagen de fondo guardada."
        )

    fondo_bytes = ruta_fondo.read_bytes()
    avatar_bytes = await usuario.display_avatar.read()

    imagen = generar_bienvenida(
        fondo_bytes=fondo_bytes,
        avatar_bytes=avatar_bytes,
        nombre_usuario=usuario.display_name,
        numero_miembro=guild.member_count or 1,
        nombre_servidor=guild.name,
        fondo_x=int(datos.get("background_x", 0)),
        fondo_y=int(datos.get("background_y", 0)),
        fondo_zoom=float(
            datos.get("background_zoom", 1.0)
        ),
        avatar_x=int(datos.get("avatar_x", 0)),
        avatar_y=int(datos.get("avatar_y", 0)),
        avatar_size=int(datos.get("avatar_size", 235)),
    )

    return discord.File(
        imagen,
        filename="welcome-editor.png",
    )


class EditorPrincipalView(discord.ui.View):
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
        label="Fondo",
        emoji="🖼️",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def fondo(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        from views.background_view import EditorFondoView

        datos = obtener_configuracion_servidor(
            self.guild.id
        )

        vista = EditorFondoView(
            bot=self.bot,
            guild=self.guild,
            usuario=self.usuario,
        )

        try:
            archivo = await generar_archivo_editor(
                self.guild,
                self.usuario,
            )

            await interaction.response.edit_message(
                content=vista.texto_estado(datos),
                attachments=[archivo],
                view=vista,
            )

        except Exception as error:
            await interaction.response.send_message(
                f"❌ No se pudo abrir el editor del fondo: `{error}`",
                ephemeral=True,
            )

    @discord.ui.button(
        label="Avatar",
        emoji="😀",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def avatar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        from views.avatar_view import EditorAvatarView

        datos = obtener_configuracion_servidor(
            self.guild.id
        )

        vista = EditorAvatarView(
            bot=self.bot,
            guild=self.guild,
            usuario=self.usuario,
        )

        try:
            archivo = await generar_archivo_editor(
                self.guild,
                self.usuario,
            )

            await interaction.response.edit_message(
                content=vista.texto_estado(datos),
                attachments=[archivo],
                view=vista,
            )

        except Exception as error:
            await interaction.response.send_message(
                f"❌ No se pudo abrir el editor del avatar: `{error}`",
                ephemeral=True,
            )

    @discord.ui.button(
        label="Texto",
        emoji="🔤",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def texto(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        from views.text_view import EditorTextoView

        vista = EditorTextoView(
            bot=self.bot,
            guild=self.guild,
            usuario=self.usuario,
        )

        await interaction.response.edit_message(
            content=(
                "🔤 **Editor del texto**\n\n"
                "Esta sección está preparada para el próximo paso."
            ),
            view=vista,
        )

    @discord.ui.button(
        label="Efectos",
        emoji="✨",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def efectos(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        from views.effects_view import EditorEfectosView

        vista = EditorEfectosView(
            bot=self.bot,
            guild=self.guild,
            usuario=self.usuario,
        )

        await interaction.response.edit_message(
            content=(
                "✨ **Editor de efectos**\n\n"
                "Aquí agregaremos sombras, brillos y partículas."
            ),
            view=vista,
        )

    @discord.ui.button(
        label="Actualizar vista",
        emoji="🔄",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def actualizar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        try:
            archivo = await generar_archivo_editor(
                self.guild,
                self.usuario,
            )

            await interaction.response.edit_message(
                content=self.texto_principal(),
                attachments=[archivo],
                view=self,
            )

        except Exception as error:
            await interaction.response.send_message(
                f"❌ No se pudo actualizar la vista: `{error}`",
                ephemeral=True,
            )

    @discord.ui.button(
        label="Cerrar",
        emoji="✅",
        style=discord.ButtonStyle.success,
        row=2,
    )
    async def cerrar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        for componente in self.children:
            componente.disabled = True

        await interaction.response.edit_message(
            content=(
                "✅ **Editor cerrado.**\n"
                "Todos los cambios quedaron guardados automáticamente."
            ),
            view=self,
        )

        self.stop()

    def texto_principal(self) -> str:
        return (
            "🎨 **Welcome Studio Editor**\n"
            "**Creado por Blasko**\n\n"
            "Selecciona el elemento que deseas modificar:\n\n"
            "🖼️ **Fondo** — posición y zoom\n"
            "😀 **Avatar** — posición y tamaño\n"
            "🔤 **Texto** — próximamente\n"
            "✨ **Efectos** — próximamente"
        )

    async def on_timeout(self) -> None:
        for componente in self.children:
            componente.disabled = True