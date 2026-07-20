import json
from pathlib import Path
from typing import Any


CARPETA_PROYECTO = Path(__file__).resolve().parent.parent
CARPETA_DATA = CARPETA_PROYECTO / "data"
ARCHIVO_CONFIG = CARPETA_DATA / "settings.json"


CONFIGURACION_PREDETERMINADA: dict[str, Any] = {
    "channel_id": None,
    "channel_name": None,
    "enabled": False,

    "background_path": None,
    "background_filename": None,
    "background_x": 0,
    "background_y": 0,
    "background_zoom": 1.0,

    "avatar_x": 0,
    "avatar_y": 0,
    "avatar_size": 235,

    "text_x": 0,
    "text_y": 0,

    "style": "anime",
}


def asegurar_archivo_configuracion() -> None:
    CARPETA_DATA.mkdir(parents=True, exist_ok=True)

    if not ARCHIVO_CONFIG.exists():
        with ARCHIVO_CONFIG.open("w", encoding="utf-8") as archivo:
            json.dump({}, archivo, ensure_ascii=False, indent=2)


def cargar_configuracion() -> dict[str, Any]:
    asegurar_archivo_configuracion()

    try:
        with ARCHIVO_CONFIG.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        return datos if isinstance(datos, dict) else {}

    except (json.JSONDecodeError, OSError) as error:
        print(f"No se pudo leer settings.json: {error}")
        return {}


def guardar_configuracion(configuracion: dict[str, Any]) -> bool:
    asegurar_archivo_configuracion()

    try:
        with ARCHIVO_CONFIG.open("w", encoding="utf-8") as archivo:
            json.dump(
                configuracion,
                archivo,
                ensure_ascii=False,
                indent=2,
            )

        return True

    except OSError as error:
        print(f"No se pudo guardar settings.json: {error}")
        return False


def obtener_configuracion_servidor(guild_id: int) -> dict[str, Any]:
    configuracion = cargar_configuracion()
    servidor_id = str(guild_id)

    datos_actuales = configuracion.get(servidor_id, {})

    datos_completos = {
        **CONFIGURACION_PREDETERMINADA,
        **datos_actuales,
    }

    if datos_completos != datos_actuales:
        configuracion[servidor_id] = datos_completos
        guardar_configuracion(configuracion)

    return datos_completos


def actualizar_configuracion_servidor(
    guild_id: int,
    **cambios: Any,
) -> dict[str, Any]:
    configuracion = cargar_configuracion()
    servidor_id = str(guild_id)

    datos_actuales = configuracion.get(servidor_id, {})

    datos_completos = {
        **CONFIGURACION_PREDETERMINADA,
        **datos_actuales,
        **cambios,
    }

    configuracion[servidor_id] = datos_completos
    guardar_configuracion(configuracion)

    return datos_completos