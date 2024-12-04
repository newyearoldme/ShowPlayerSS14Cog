import discord
from discord.ext import commands
from utils.config_loader import load_online_bots_config
from HTTPrequest import fetch_player_list
import os

# Загружаем конфигурацию серверов
CONFIG_PATH = os.path.join("utils", "online_servers_bots.json")
try:
    servers = load_online_bots_config(CONFIG_PATH)
except (FileNotFoundError, ValueError) as e:
    print(f"Ошибка загрузки конфигурации серверов: {e}")
    servers = []

class PlayerListCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.slash_command(
        description="Получить информацию об игроках на выбранном сервере."
    )
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def player_list(self, ctx: discord.ApplicationContext, server: str = discord.Option(description="Выберите сервер", choices=[srv.name for srv in servers]),
    ):
        await ctx.defer()
        # Получаем данные о выбранном сервере
        selected_server = next((srv for srv in servers if srv.name == server), None)
        if not selected_server:
            await ctx.respond("Указанный сервер не найден", ephemeral=True)
            return

        # Выполняем запрос к API для выбранного сервера
        result = fetch_player_list(selected_server)

        if isinstance(result, dict) and "error" in result:
            await ctx.respond(f"Ошибка: {result['error']}", ephemeral=True)
            return

        if not result:
            await ctx.respond(f"На сервере **{selected_server.name}** нет обычных игроков")
            return

        embed = discord.Embed(
            title=f"Игроки на сервере {selected_server.name}",
            description="Список обычных игроков:",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"IP сервера: {selected_server.ip}")

        for player in result:
            embed.add_field(
                name=player["Name"], 
                value=f"UserID: {player['UserId']}", 
                inline=False
            )

        await ctx.respond(embed=embed)

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Команда на кулдауне. Попробуйте снова через {round(error.retry_after, 2)} сек.", ephemeral=True)
        else:
            raise error

def setup(client):
    client.add_cog(PlayerListCog(client))
