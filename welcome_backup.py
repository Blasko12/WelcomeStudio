import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from io import BytesIO

from image_generator import generar_bienvenida


CARPETA_PROYECTO = Path(__file__).parent
ARCHIVO_CONFIG = CARPETA_PROYECTO / "data" / "settings.json"
CARPETA_FONDOS = CARPETA_PROYECTO / "assets" / "backgrounds"

EXTENSIONES_PERMITIDAS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

TAMANO_MAXIMO = 8 * 1024 * 1024  # 8 MB


def cargar_configuracion() -> dict:
    if not ARCHIVO_CONFIG.exists():
        return {}

    try:
        with ARCHIVO_CONFIG.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        return datos if isinstance(datos, dict) else {}

    except (json.JSONDecodeError, OSError):
        return {}


def guardar_configuracion(datos: dict) -> None:
    ARCHIVO_CONFIG.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with ARCHIVO_CONFIG.open("w", encoding="utf-8") as archivo:
        json.dump(
            datos,
            archivo,
            ensure_ascii=False,
            indent=2,
        )


def obtener_configuracion_servidor(
    configuracion: dict,
    guild_id: int,
) -> dict:
    servidor_id = str(guild_id)

    if servidor_id not in configuracion:
        configuracion[servidor_id] = {
            "enabled": False,
            "channel_id": None,
            "channel_name": None,
            "background_path": None,
        }

    return configuracion[servidor_id]


def borrar_fondo_anterior(guild_id: int) -> None:
    """
    Elimina fondos antiguos del mismo servidor para evitar
    conservar varias versiones innecesarias.
    """

    CARPETA_FONDOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    for extension in EXTENSIONES_PERMITIDAS:
        archivo = CARPETA_FONDOS / f"{guild_id}{extension}"

        if archivo.exists():
            archivo.unlink()


class WelcomeEvents(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ======================================================
    # /CONFIGURAR
    # ======================================================

    @app_commands.command(
        name="configurar",
        description="Selecciona el canal donde llegarán las bienvenidas.",
    )
    @app_commands.describe(
        canal="Canal donde Welcome Studio enviará las bienvenidas."
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
                "Este comando solo funciona dentro de un servidor.",
                ephemeral=True,
            )
            return

        configuracion = cargar_configuracion()

        datos_servidor = obtener_configuracion_servidor(
            configuracion,
            interaction.guild.id,
        )

        datos_servidor["channel_id"] = canal.id
        datos_servidor["channel_name"] = canal.name
        datos_servidor["enabled"] = True

        guardar_configuracion(configuracion)

        await interaction.response.send_message(
            f"✅ {canal.mention} fue configurado como canal "
            "de bienvenidas.",
            ephemeral=True,
        )

    # ======================================================
    # /FONDO
    # ======================================================

    @app_commands.command(
        name="fondo",
        description="Sube una imagen para usarla como fondo de bienvenida.",
    )
    @app_commands.describe(
        imagen="Imagen PNG, JPG, JPEG o WEBP que se usará de fondo."
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
                "Este comando solo funciona dentro de un servidor.",
                ephemeral=True,
            )
            return

        extension = Path(imagen.filename).suffix.lower()
        tipo_contenido = imagen.content_type or ""

        if (
            extension not in EXTENSIONES_PERMITIDAS
            or not tipo_contenido.startswith("image/")
        ):
            await interaction.response.send_message(
                "❌ El archivo debe ser una imagen PNG, JPG, JPEG "
                "o WEBP.",
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

        borrar_fondo_anterior(
            interaction.guild.id
        )

        nombre_archivo = (
            f"{interaction.guild.id}{extension}"
        )

        ruta_fondo = (
            CARPETA_FONDOS / nombre_archivo
        )

        try:
            await imagen.save(ruta_fondo)

        except (discord.HTTPException, OSError) as error:
            await interaction.followup.send(
                f"❌ No se pudo guardar la imagen: `{error}`",
                ephemeral=True,
            )
            return

        configuracion = cargar_configuracion()

        datos_servidor = obtener_configuracion_servidor(
            configuracion,
            interaction.guild.id,
        )

        datos_servidor["background_path"] = str(
            ruta_fondo.relative_to(CARPETA_PROYECTO)
        )

        datos_servidor["background_filename"] = (
            imagen.filename
        )

        guardar_configuracion(configuracion)

        archivo_confirmacion = discord.File(
            ruta_fondo,
            filename=nombre_archivo,
        )

        embed = discord.Embed(
            title="🖼️ Fondo actualizado",
            description=(
                "Esta imagen se utilizará como fondo para "
                "las bienvenidas del servidor."
            ),
            color=0x5865F2,
        )

        embed.set_image(
            url=f"attachment://{nombre_archivo}"
        )

        embed.set_footer(
            text="Welcome Studio • Configuración guardada"
        )

        await interaction.followup.send(
            embed=embed,
            file=archivo_confirmacion,
            ephemeral=True,
        )

 # ======================================================
    # /PREVIEW
    # ======================================================

    @app_commands.command(
        name="preview",
        description="Muestra una vista previa de la bienvenida.",
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
                "Este comando solo funciona dentro de un servidor.",
                ephemeral=True,
            )
            return

        if not isinstance(
            interaction.user,
            discord.Member,
        ):
            await interaction.response.send_message(
                "No se pudo obtener tu información de miembro.",
                ephemeral=True,
            )
            return

        configuracion = cargar_configuracion()

        datos_servidor = configuracion.get(
            str(interaction.guild.id)
        )

        if not datos_servidor:
            await interaction.response.send_message(
                "❌ Primero debes ejecutar `/configurar`.",
                ephemeral=True,
            )
            return

        ruta_relativa = datos_servidor.get(
            "background_path"
        )

        if not ruta_relativa:
            await interaction.response.send_message(
                "❌ Primero debes subir un fondo con `/fondo`.",
                ephemeral=True,
            )
            return

        ruta_fondo = (
            CARPETA_PROYECTO / ruta_relativa
        )

        if not ruta_fondo.exists():
            await interaction.response.send_message(
                "❌ No se encontró el fondo guardado. "
                "Vuelve a utilizar `/fondo`.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:
            fondo_bytes = ruta_fondo.read_bytes()

            avatar_bytes = await (
                interaction.user.display_avatar.read()
            )

            imagen = generar_bienvenida(
                fondo_bytes=fondo_bytes,
                avatar_bytes=avatar_bytes,
                nombre_usuario=interaction.user.display_name,
                numero_miembro=interaction.guild.member_count,
                nombre_servidor=interaction.guild.name,
            )

        except Exception as error:
            await interaction.followup.send(
                f"❌ No se pudo generar la imagen: `{error}`",
                ephemeral=True,
            )
            return

        archivo = discord.File(
            imagen,
            filename="welcome-preview.png",
        )

        await interaction.followup.send(
            content="👀 **Vista previa del estilo Anime**",
            file=archivo,
            ephemeral=True,
        )
        
    # ======================================================
    # ERRORES DE COMANDOS
    # ======================================================

    async def responder_error_permisos(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
        comando: str,
    ) -> None:
        if isinstance(
            error,
            app_commands.MissingPermissions,
        ):
            mensaje = (
                f"Solo un administrador puede utilizar `/{comando}`."
            )
        else:
            mensaje = (
                f"No se pudo ejecutar `/{comando}`: `{error}`"
            )

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

    @configurar.error
    async def configurar_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await self.responder_error_permisos(
            interaction,
            error,
            "configurar",
        )

    @fondo.error
    async def fondo_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await self.responder_error_permisos(
            interaction,
            error,
            "fondo",
        )

    # ======================================================
    # EVENTO DE BIENVENIDA
    # ======================================================

    @commands.Cog.listener()
    async def on_member_join(
        self,
        member: discord.Member,
    ) -> None:
        configuracion = cargar_configuracion()

        datos_servidor = configuracion.get(
            str(member.guild.id)
        )

        if not datos_servidor:
            print(
                f"{member.guild.name} no tiene configuración."
            )
            return

        if not datos_servidor.get(
            "enabled",
            False,
        ):
            print(
                f"Las bienvenidas están desactivadas en "
                f"{member.guild.name}."
            )
            return

        channel_id = datos_servidor.get(
            "channel_id"
        )

        try:
            channel_id = int(channel_id)
        except (TypeError, ValueError):
            print(
                f"El canal configurado no es válido en "
                f"{member.guild.name}."
            )
            return

        canal = member.guild.get_channel(
            channel_id
        )

        if canal is None:
            try:
                canal = await self.bot.fetch_channel(
                    channel_id
                )
            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException,
            ):
                print(
                    f"No se pudo encontrar el canal "
                    f"{channel_id}."
                )
                return

        try:
            await canal.send(
                f"👋 ¡Bienvenido {member.mention} a "
                f"**{member.guild.name}**!\n"
                f"Ahora somos "
                f"**{member.guild.member_count} miembros**."
            )

            print(
                f"Bienvenida enviada para {member} "
                f"en {member.guild.name}."
            )

        except discord.Forbidden:
            print(
                f"Welcome Studio no puede escribir "
                f"en el canal {channel_id}."
            )

        except discord.HTTPException as error:
            print(
                f"Discord rechazó la bienvenida: {error}"
            )



async def setup(
    bot: commands.Bot,
) -> None:
    await bot.add_cog(
        WelcomeEvents(bot)
    )

    