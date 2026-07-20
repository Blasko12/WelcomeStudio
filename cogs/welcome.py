from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from image_generator import generar_bienvenida
from utils.config_manager import (
    actualizar_configuracion_servidor,
    obtener_configuracion_servidor,
)
from views.editor_view import EditorPrincipalView


CARPETA_PROYECTO = Path(__file__).resolve().parent.parent
CARPETA_FONDOS = CARPETA_PROYECTO / "assets" / "backgrounds"

EXTENSIONES_PERMITIDAS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

TAMANO_MAXIMO = 8 * 1024 * 1024


def borrar_fondos_anteriores(guild_id: int) -> None:
    """
    Elimina el fondo anterior del servidor para evitar
    guardar varias imágenes innecesarias.
    """

    CARPETA_FONDOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    for extension in EXTENSIONES_PERMITIDAS:
        ruta = CARPETA_FONDOS / f"{guild_id}{extension}"

        if ruta.exists():
            try:
                ruta.unlink()
            except OSError as error:
                print(
                    f"No se pudo eliminar el fondo anterior "
                    f"{ruta}: {error}"
                )


class WelcomeCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
    ) -> None:
        self.bot = bot

    async def generar_imagen(
        self,
        guild: discord.Guild,
        miembro: discord.Member,
    ):
        """
        Genera la imagen de bienvenida usando la configuración
        guardada para el servidor.
        """

        datos = obtener_configuracion_servidor(
            guild.id
        )

        ruta_relativa = datos.get(
            "background_path"
        )

        if not ruta_relativa:
            raise FileNotFoundError(
                "No hay un fondo configurado. Usa `/fondo`."
            )

        ruta_fondo = (
            CARPETA_PROYECTO / ruta_relativa
        )

        if not ruta_fondo.exists():
            raise FileNotFoundError(
                "No se encontró el archivo del fondo. "
                "Vuelve a utilizar `/fondo`."
            )

        fondo_bytes = ruta_fondo.read_bytes()

        avatar_bytes = await (
            miembro.display_avatar.read()
        )

        return generar_bienvenida(
            fondo_bytes=fondo_bytes,
            avatar_bytes=avatar_bytes,
            nombre_usuario=miembro.display_name,
            numero_miembro=guild.member_count or 1,
            nombre_servidor=guild.name,
            fondo_x=int(
                datos.get(
                    "background_x",
                    0,
                )
            ),
            fondo_y=int(
                datos.get(
                    "background_y",
                    0,
                )
            ),
            fondo_zoom=float(
                datos.get(
                    "background_zoom",
                    1.0,
                )
            ),
            avatar_x=int(datos.get("avatar_x", 0)),
            avatar_y=int(datos.get("avatar_y", 0)),
            avatar_size=int(
                datos.get("avatar_size", 235)
            ),
        )

    # ======================================================
    # COMANDO /CONFIGURAR
    # ======================================================

    @app_commands.command(
        name="configurar",
        description=(
            "Configura el canal donde se enviarán las bienvenidas."
        ),
    )
    @app_commands.describe(
        canal=(
            "Canal donde Welcome Studio enviará las bienvenidas."
        )
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def configurar(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solo puede utilizarse "
                "dentro de un servidor.",
                ephemeral=True,
            )
            return

        permisos = canal.permissions_for(
            interaction.guild.me
        )

        if not permisos.view_channel:
            await interaction.response.send_message(
                f"❌ No tengo permiso para ver {canal.mention}.",
                ephemeral=True,
            )
            return

        if not permisos.send_messages:
            await interaction.response.send_message(
                f"❌ No tengo permiso para enviar mensajes "
                f"en {canal.mention}.",
                ephemeral=True,
            )
            return

        if not permisos.attach_files:
            await interaction.response.send_message(
                f"❌ Necesito el permiso **Adjuntar archivos** "
                f"en {canal.mention}.",
                ephemeral=True,
            )
            return

        actualizar_configuracion_servidor(
            interaction.guild.id,
            channel_id=canal.id,
            channel_name=canal.name,
            enabled=True,
        )

        await interaction.response.send_message(
            f"✅ {canal.mention} fue configurado como canal "
            "de bienvenidas.\n\n"
            "Ahora utiliza `/fondo` para subir una imagen.",
            ephemeral=True,
        )

        print(
            f"Canal configurado en {interaction.guild.name}: "
            f"#{canal.name}"
        )

    # ======================================================
    # COMANDO /FONDO
    # ======================================================

    @app_commands.command(
        name="fondo",
        description=(
            "Sube una imagen para usarla como fondo "
            "de las bienvenidas."
        ),
    )
    @app_commands.describe(
        imagen=(
            "Imagen PNG, JPG, JPEG o WEBP de máximo 8 MB."
        )
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def fondo(
        self,
        interaction: discord.Interaction,
        imagen: discord.Attachment,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solo puede utilizarse "
                "dentro de un servidor.",
                ephemeral=True,
            )
            return

        extension = Path(
            imagen.filename
        ).suffix.lower()

        tipo_contenido = (
            imagen.content_type or ""
        ).lower()

        if extension not in EXTENSIONES_PERMITIDAS:
            await interaction.response.send_message(
                "❌ El archivo debe ser PNG, JPG, JPEG o WEBP.",
                ephemeral=True,
            )
            return

        if (
            tipo_contenido
            and not tipo_contenido.startswith("image/")
        ):
            await interaction.response.send_message(
                "❌ El archivo seleccionado no parece ser "
                "una imagen válida.",
                ephemeral=True,
            )
            return

        if imagen.size > TAMANO_MAXIMO:
            await interaction.response.send_message(
                "❌ La imagen supera el límite de 8 MB.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        CARPETA_FONDOS.mkdir(
            parents=True,
            exist_ok=True,
        )

        borrar_fondos_anteriores(
            interaction.guild.id
        )

        nombre_guardado = (
            f"{interaction.guild.id}{extension}"
        )

        ruta_fondo = (
            CARPETA_FONDOS / nombre_guardado
        )

        try:
            await imagen.save(
                ruta_fondo
            )

        except (
            discord.HTTPException,
            OSError,
        ) as error:
            await interaction.followup.send(
                f"❌ No se pudo guardar la imagen: `{error}`",
                ephemeral=True,
            )
            return

        ruta_relativa = str(
            ruta_fondo.relative_to(
                CARPETA_PROYECTO
            )
        )

        actualizar_configuracion_servidor(
            interaction.guild.id,
            background_path=ruta_relativa,
            background_filename=imagen.filename,
            background_x=0,
            background_y=0,
            background_zoom=1.0,
        )

        archivo = discord.File(
            ruta_fondo,
            filename=nombre_guardado,
        )

        embed = discord.Embed(
            title="🖼️ Fondo actualizado",
            description=(
                "La imagen fue guardada correctamente.\n\n"
                "Usa `/preview` para ver la bienvenida o "
                "`/editor` para ajustar el encuadre."
            ),
            color=0x5865F2,
        )

        embed.set_image(
            url=f"attachment://{nombre_guardado}"
        )

        embed.set_footer(
            text="Welcome Studio • Creado por Blasko"
        )

        await interaction.followup.send(
            embed=embed,
            file=archivo,
            ephemeral=True,
        )

        print(
            f"Fondo actualizado en "
            f"{interaction.guild.name}: "
            f"{imagen.filename}"
        )
          # ======================================================
    # COMANDO /PREVIEW
    # ======================================================

    @app_commands.command(
        name="preview",
        description=(
            "Muestra una vista previa de la bienvenida."
        ),
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def preview(
        self,
        interaction: discord.Interaction,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solo puede utilizarse "
                "dentro de un servidor.",
                ephemeral=True,
            )
            return

        if not isinstance(
            interaction.user,
            discord.Member,
        ):
            await interaction.response.send_message(
                "❌ No se pudo obtener tu información "
                "como miembro del servidor.",
                ephemeral=True,
            )
            return

        datos = obtener_configuracion_servidor(
            interaction.guild.id
        )

        if not datos.get("background_path"):
            await interaction.response.send_message(
                "❌ Primero debes subir una imagen "
                "utilizando `/fondo`.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:
            imagen = await self.generar_imagen(
                guild=interaction.guild,
                miembro=interaction.user,
            )

            archivo = discord.File(
                imagen,
                filename="welcome-preview.png",
            )

            embed = discord.Embed(
                title="👀 Vista previa",
                description=(
                    "Así se verá la bienvenida cuando "
                    "entre una persona al servidor."
                ),
                color=0x5865F2,
            )

            embed.set_image(
                url="attachment://welcome-preview.png"
            )

            embed.set_footer(
                text="Welcome Studio • Creado por Blasko"
            )

            await interaction.followup.send(
                embed=embed,
                file=archivo,
                ephemeral=True,
            )

        except FileNotFoundError as error:
            await interaction.followup.send(
                f"❌ {error}",
                ephemeral=True,
            )

        except Exception as error:
            print(
                f"Error generando la vista previa: {error}"
            )

            await interaction.followup.send(
                f"❌ No se pudo generar la vista previa: "
                f"`{error}`",
                ephemeral=True,
            )

    # ======================================================
    # COMANDO /EDITOR
    # ======================================================

    @app_commands.command(
        name="editor",
        description=(
            "Abre el editor visual de la bienvenida."
        ),
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def editor(
        self,
        interaction: discord.Interaction,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solo puede utilizarse "
                "dentro de un servidor.",
                ephemeral=True,
            )
            return

        if not isinstance(
            interaction.user,
            discord.Member,
        ):
            await interaction.response.send_message(
                "❌ No se pudo obtener tu información "
                "como miembro del servidor.",
                ephemeral=True,
            )
            return

        datos = obtener_configuracion_servidor(
            interaction.guild.id
        )

        if not datos.get("background_path"):
            await interaction.response.send_message(
                "❌ Primero debes subir una imagen "
                "utilizando `/fondo`.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        vista = EditorPrincipalView(
            bot=self.bot,
            guild=interaction.guild,
            usuario=interaction.user,
        )

        try:
            imagen = await self.generar_imagen(
                guild=interaction.guild,
                miembro=interaction.user,
            )

            archivo = discord.File(
                imagen,
                filename="welcome-editor.png",
            )

            embed = discord.Embed(
                title="🎨 Welcome Studio Editor",
                description=(
                    "Selecciona el elemento que deseas modificar.\n\n"
                    "🖼️ **Fondo**\n"
                    "Mueve la imagen y cambia el zoom.\n\n"
                    "😀 **Avatar**\n"
                    "Próximamente podrás moverlo y cambiar "
                    "su tamaño.\n\n"
                    "🔤 **Texto**\n"
                    "Próximamente podrás modificar su posición."
                ),
                color=0x5865F2,
            )

            embed.set_image(
                url="attachment://welcome-editor.png"
            )

            embed.set_footer(
                text="Welcome Studio • Creado por Blasko"
            )

            await interaction.followup.send(
                embed=embed,
                file=archivo,
                view=vista,
                ephemeral=True,
            )

        except FileNotFoundError as error:
            await interaction.followup.send(
                f"❌ {error}",
                ephemeral=True,
            )

        except Exception as error:
            print(
                f"Error abriendo el editor: {error}"
            )

            await interaction.followup.send(
                f"❌ No se pudo abrir el editor: `{error}`",
                ephemeral=True,
            )
             # ======================================================
    # EVENTO: NUEVO MIEMBRO
    # ======================================================

    @commands.Cog.listener()
    async def on_member_join(
        self,
        member: discord.Member,
    ) -> None:
        datos = obtener_configuracion_servidor(
            member.guild.id
        )

        if not datos.get("enabled", False):
            return

        channel_id = datos.get("channel_id")

        if channel_id is None:
            return

        try:
            canal = member.guild.get_channel(
                int(channel_id)
            )

            if canal is None:
                canal = await self.bot.fetch_channel(
                    int(channel_id)
                )

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
            ValueError,
        ):
            print(
                f"No se pudo obtener el canal "
                f"de bienvenida del servidor "
                f"{member.guild.name}"
            )
            return

        if not isinstance(
            canal,
            discord.TextChannel,
        ):
            return

        try:
            imagen = await self.generar_imagen(
                guild=member.guild,
                miembro=member,
            )

            archivo = discord.File(
                imagen,
                filename="bienvenida.png",
            )

            embed = discord.Embed(
                title="🎉 ¡Bienvenido!",
                description=(
                    f"Nos alegra tenerte aquí "
                    f"{member.mention}\n\n"
                    "Esperamos que disfrutes tu estancia."
                ),
                color=0x5865F2,
            )

            embed.set_image(
                url="attachment://bienvenida.png"
            )

            embed.set_footer(
                text="Welcome Studio • Creado por Blasko"
            )

            await canal.send(
                embed=embed,
                file=archivo,
                allowed_mentions=discord.AllowedMentions(
                    users=True,
                    everyone=False,
                    roles=False,
                ),
            )

            print(
                f"Bienvenida enviada para "
                f"{member} en "
                f"{member.guild.name}"
            )

        except Exception as error:
            print(
                f"Error enviando la bienvenida: "
                f"{error}"
            )
            # ======================================================
    # MANEJO DE ERRORES
    # ======================================================

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        if isinstance(
            error,
            app_commands.MissingPermissions,
        ):
            mensaje = (
                "❌ Solo un administrador puede utilizar este comando."
            )

        elif isinstance(
            error,
            app_commands.CommandOnCooldown,
        ):
            mensaje = (
                f"⏳ Espera "
                f"{error.retry_after:.1f} segundos "
                "antes de volver a utilizar este comando."
            )

        else:
            print(
                "Error en comando:",
                repr(error),
            )

            mensaje = (
                "❌ Ocurrió un error inesperado.\n"
                "Revisa la consola para obtener más información."
            )

        try:
            if interaction.response.is_done():
                await interaction.followup.send(
                    mensaje,
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    mensaje,
                    ephemeral=True,
                )

        except Exception as e:
            print(
                f"No se pudo enviar el mensaje "
                f"de error: {e}"
            )


# ==========================================================
# CARGAR EL COG
# ==========================================================

async def setup(
    bot: commands.Bot,
) -> None:
    await bot.add_cog(
        WelcomeCog(bot)
    )

    print(
        "Módulo Welcome Studio cargado."
    )