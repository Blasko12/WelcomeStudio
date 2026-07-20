from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ANCHO_IMAGEN = 1200
ALTO_IMAGEN = 675

CARPETA_PROYECTO = Path(__file__).parent
CARPETA_FUENTES = CARPETA_PROYECTO / "assets" / "fonts"


def buscar_fuente(negrita: bool = False) -> str | None:
    if negrita:
        nombres = [
            "DejaVuSans-Bold.ttf",
            "arialbd.ttf",
        ]
    else:
        nombres = [
            "DejaVuSans.ttf",
            "arial.ttf",
        ]

    rutas_posibles: list[Path] = []

    for nombre in nombres:
        rutas_posibles.extend(
            [
                CARPETA_FUENTES / nombre,
                Path("C:/Windows/Fonts") / nombre,
                Path("/usr/share/fonts/truetype/dejavu") / nombre,
            ]
        )

    for ruta in rutas_posibles:
        if ruta.exists():
            return str(ruta)

    return None


def cargar_fuente(
    tamano: int,
    negrita: bool = False,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    ruta = buscar_fuente(negrita)

    if ruta:
        return ImageFont.truetype(ruta, tamano)

    return ImageFont.load_default()


def limitar_texto(texto: str, limite: int) -> str:
    texto = texto.strip()

    if len(texto) <= limite:
        return texto

    return texto[: limite - 3] + "..."


def ajustar_fondo(
    imagen: Image.Image,
    offset_x: int = 0,
    offset_y: int = 0,
    zoom: float = 1.0,
) -> Image.Image:
    imagen = imagen.convert("RGB")

    zoom = max(1.0, min(float(zoom), 3.0))

    escala_base = max(
        ANCHO_IMAGEN / imagen.width,
        ALTO_IMAGEN / imagen.height,
    )

    escala_final = escala_base * zoom

    nuevo_ancho = max(
        ANCHO_IMAGEN,
        int(imagen.width * escala_final),
    )

    nuevo_alto = max(
        ALTO_IMAGEN,
        int(imagen.height * escala_final),
    )

    imagen = imagen.resize(
        (nuevo_ancho, nuevo_alto),
        Image.Resampling.LANCZOS,
    )

    x = (
        (ANCHO_IMAGEN - nuevo_ancho) // 2
        + int(offset_x)
    )

    y = (
        (ALTO_IMAGEN - nuevo_alto) // 2
        + int(offset_y)
    )

    x_minimo = ANCHO_IMAGEN - nuevo_ancho
    y_minimo = ALTO_IMAGEN - nuevo_alto

    x = max(x_minimo, min(0, x))
    y = max(y_minimo, min(0, y))

    lienzo = Image.new(
        "RGB",
        (ANCHO_IMAGEN, ALTO_IMAGEN),
        (0, 0, 0),
    )

    lienzo.paste(imagen, (x, y))

    return lienzo


def crear_avatar_circular(
    avatar: Image.Image,
    tamano: int,
) -> Image.Image:
    avatar = avatar.convert("RGBA")

    lado = min(avatar.width, avatar.height)

    izquierda = (avatar.width - lado) // 2
    arriba = (avatar.height - lado) // 2

    avatar = avatar.crop(
        (
            izquierda,
            arriba,
            izquierda + lado,
            arriba + lado,
        )
    )

    avatar = avatar.resize(
        (tamano, tamano),
        Image.Resampling.LANCZOS,
    )

    mascara = Image.new(
        "L",
        (tamano, tamano),
        0,
    )

    dibujo_mascara = ImageDraw.Draw(mascara)

    dibujo_mascara.ellipse(
        (0, 0, tamano - 1, tamano - 1),
        fill=255,
    )

    resultado = Image.new(
        "RGBA",
        (tamano, tamano),
        (0, 0, 0, 0),
    )

    resultado.paste(
        avatar,
        (0, 0),
        mascara,
    )

    return resultado


def crear_sombra_avatar(tamano_avatar: int) -> Image.Image:
    margen = 45
    tamano_total = tamano_avatar + margen * 2

    sombra = Image.new(
        "RGBA",
        (tamano_total, tamano_total),
        (0, 0, 0, 0),
    )

    dibujo = ImageDraw.Draw(sombra)

    dibujo.ellipse(
        (
            margen,
            margen,
            margen + tamano_avatar,
            margen + tamano_avatar,
        ),
        fill=(0, 0, 0, 220),
    )

    return sombra.filter(
        ImageFilter.GaussianBlur(18)
    )


def crear_borde_avatar(
    tamano_avatar: int,
    grosor: int = 8,
) -> Image.Image:
    tamano_total = tamano_avatar + grosor * 2

    borde = Image.new(
        "RGBA",
        (tamano_total, tamano_total),
        (0, 0, 0, 0),
    )

    dibujo = ImageDraw.Draw(borde)

    dibujo.ellipse(
        (
            0,
            0,
            tamano_total - 1,
            tamano_total - 1,
        ),
        fill=(255, 255, 255, 255),
    )

    return borde


def dibujar_texto_centrado(
    dibujo: ImageDraw.ImageDraw,
    texto: str,
    y: int,
    fuente,
    color=(255, 255, 255, 255),
    sombra: bool = True,
    grosor_borde: int = 1,
) -> None:
    caja = dibujo.textbbox(
        (0, 0),
        texto,
        font=fuente,
        stroke_width=grosor_borde,
    )

    ancho_texto = caja[2] - caja[0]
    x = (ANCHO_IMAGEN - ancho_texto) // 2

    if sombra:
        dibujo.text(
            (x + 4, y + 4),
            texto,
            font=fuente,
            fill=(0, 0, 0, 210),
            stroke_width=3,
            stroke_fill=(0, 0, 0, 210),
        )

    dibujo.text(
        (x, y),
        texto,
        font=fuente,
        fill=color,
        stroke_width=grosor_borde,
        stroke_fill=(0, 0, 0, 210),
    )


def crear_capa_oscura() -> Image.Image:
    return Image.new(
        "RGBA",
        (ANCHO_IMAGEN, ALTO_IMAGEN),
        (0, 0, 0, 55),
    )


def crear_degradado_inferior() -> Image.Image:
    degradado = Image.new(
        "RGBA",
        (ANCHO_IMAGEN, ALTO_IMAGEN),
        (0, 0, 0, 0),
    )

    dibujo = ImageDraw.Draw(degradado)
    inicio = 250

    for y in range(inicio, ALTO_IMAGEN):
        progreso = (
            (y - inicio)
            / (ALTO_IMAGEN - inicio)
        )

        alpha = int(20 + 150 * progreso)

        dibujo.line(
            [(0, y), (ANCHO_IMAGEN, y)],
            fill=(0, 0, 0, alpha),
        )

    return degradado


def generar_bienvenida(
    fondo_bytes: bytes,
    avatar_bytes: bytes,
    nombre_usuario: str,
    numero_miembro: int,
    nombre_servidor: str,
    fondo_x: int = 0,
    fondo_y: int = 0,
    fondo_zoom: float = 1.0,
    avatar_x: int = 0,
    avatar_y: int = 0,
    avatar_size: int = 235,
) -> BytesIO:
    """
    Genera la imagen de bienvenida.

    avatar_x y avatar_y desplazan el avatar desde su
    posición central original.

    avatar_size controla su tamaño.
    """

    avatar_size = max(
        100,
        min(int(avatar_size), 450),
    )

    fondo_original = Image.open(
        BytesIO(fondo_bytes)
    )

    fondo = ajustar_fondo(
        imagen=fondo_original,
        offset_x=fondo_x,
        offset_y=fondo_y,
        zoom=fondo_zoom,
    ).convert("RGBA")

    fondo = Image.alpha_composite(
        fondo,
        crear_capa_oscura(),
    )

    fondo = Image.alpha_composite(
        fondo,
        crear_degradado_inferior(),
    )

    avatar_original = Image.open(
        BytesIO(avatar_bytes)
    )

    grosor_borde = max(
        5,
        int(avatar_size * 0.035),
    )

    avatar = crear_avatar_circular(
        avatar_original,
        avatar_size,
    )

    sombra_avatar = crear_sombra_avatar(
        avatar_size
    )

    centro_x = (
        ANCHO_IMAGEN - avatar_size
    ) // 2

    posicion_avatar_x = centro_x + int(avatar_x)
    posicion_avatar_y = 75 + int(avatar_y)

    posicion_avatar_x = max(
        0,
        min(
            ANCHO_IMAGEN - avatar_size,
            posicion_avatar_x,
        ),
    )

    posicion_avatar_y = max(
        0,
        min(
            ALTO_IMAGEN - avatar_size,
            posicion_avatar_y,
        ),
    )

    posicion_sombra = (
        posicion_avatar_x
        - (sombra_avatar.width - avatar_size) // 2,
        posicion_avatar_y
        - (sombra_avatar.height - avatar_size) // 2,
    )

    fondo.alpha_composite(
        sombra_avatar,
        posicion_sombra,
    )

    borde_avatar = crear_borde_avatar(
        avatar_size,
        grosor_borde,
    )

    posicion_borde = (
        posicion_avatar_x - grosor_borde,
        posicion_avatar_y - grosor_borde,
    )

    fondo.alpha_composite(
        borde_avatar,
        posicion_borde,
    )

    fondo.alpha_composite(
        avatar,
        (
            posicion_avatar_x,
            posicion_avatar_y,
        ),
    )

    dibujo = ImageDraw.Draw(fondo)

    fuente_titulo = cargar_fuente(
        60,
        negrita=True,
    )

    fuente_usuario = cargar_fuente(
        48,
        negrita=True,
    )

    fuente_servidor = cargar_fuente(
        30,
        negrita=False,
    )

    fuente_miembro = cargar_fuente(
        26,
        negrita=True,
    )

    nombre_usuario = limitar_texto(
        nombre_usuario,
        28,
    )

    nombre_servidor = limitar_texto(
        nombre_servidor,
        40,
    )

    dibujar_texto_centrado(
        dibujo=dibujo,
        texto="¡BIENVENIDO!",
        y=340,
        fuente=fuente_titulo,
        grosor_borde=2,
    )

    dibujar_texto_centrado(
        dibujo=dibujo,
        texto=nombre_usuario,
        y=418,
        fuente=fuente_usuario,
        grosor_borde=2,
    )

    dibujar_texto_centrado(
        dibujo=dibujo,
        texto=nombre_servidor,
        y=492,
        fuente=fuente_servidor,
        color=(235, 235, 240, 255),
    )

    dibujar_texto_centrado(
        dibujo=dibujo,
        texto=f"MIEMBRO #{numero_miembro}",
        y=545,
        fuente=fuente_miembro,
        color=(230, 230, 235, 255),
    )

    salida = BytesIO()

    fondo.convert("RGB").save(
        salida,
        format="PNG",
        optimize=True,
    )

    salida.seek(0)

    return salida