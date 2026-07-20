import discord
from discord.ext import commands

from config import TOKEN
from keep_alive import mantener_activo


class WelcomeBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self) -> None:
        await self.load_extension("cogs.welcome")
        print("Módulo de bienvenidas cargado.")

        # Eliminar comandos específicos del servidor de pruebas
        # para evitar duplicados.
        for guild in self.guilds:
            self.tree.clear_commands(guild=guild)
            await self.tree.sync(guild=guild)

        # Sincronizar una sola versión global.
        comandos = await self.tree.sync()

        print(f"Comandos globales sincronizados: {len(comandos)}")


bot = WelcomeBot()


@bot.event
async def on_ready() -> None:
    print("=" * 48)
    print(f"Welcome Studio conectado como: {bot.user}")
    print(f"Servidores conectados: {len(bot.guilds)}")
    print("=" * 48)


if not TOKEN:
    raise RuntimeError(
        "No se encontró TOKEN. Revisa el archivo .env."
    )

mantener_activo()
bot.run(TOKEN)