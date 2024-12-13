import discord
from discord.ext import commands
from utils.config_loader import load_online_bots_config

if "cogs" in __name__:
    from .HTTPrequest import fetch_player_list, fetch_admin_players
else:
    from HTTPrequest import fetch_player_list, fetch_admin_players


class PlayerListCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.servers = load_online_bots_config("utils/online_servers_bots.json")

    # Автодополнение
    async def server_autocomplete(self, ctx: discord.AutocompleteContext):
        return [srv.name for srv in self.servers]

    @commands.slash_command(description="Получить список игроков или администраторов")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def show_player_list(
        self,
        ctx: discord.ApplicationContext,
        server: str = discord.Option(
            description="Выберите сервер",
            autocomplete=server_autocomplete
        ),
        list_type: str = discord.Option(
            description="Выберите тип списка",
            choices=["player_list", "admin_list"]
        ),
    ):
        await ctx.defer()

        # Обновляем список серверов
        servers = {srv.name: srv for srv in self.servers}
        if server not in servers:
            await ctx.respond("Указанный сервер не найден", ephemeral=True)
            return

        selected_server = servers[server]

        if list_type == "player_list":
            result = await fetch_player_list(selected_server)
            title = f"Игроки на сервере {selected_server.name}"
            description = "Список игроков:"
            color = discord.Color.blue()
        else:  # list_type == "admin_list"
            result = await fetch_admin_players(selected_server)
            title = f"Администраторы на сервере {selected_server.name}"
            description = "Список администраторов:"
            color = discord.Color.green()

        if isinstance(result, dict) and "error" in result:
            await ctx.respond(f"Ошибка: {result['error']}", ephemeral=True)
            return
        
        if not result:
            await ctx.respond(f"На сервере **{selected_server.name}** нет данных для выбранного типа списка", ephemeral=True)
            return

        # Формирование Embed
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=f"IP сервера: {selected_server.ip}")

        if list_type == "player_list":
            for player in result:
                embed.add_field(
                    name=player["Name"], 
                    value="\u200b", 
                    inline=False
                )
        else:  # list_type == "admin_list"
            for admin_name, details in result.items():
                admin_title = details if isinstance(details, str) else "Без поста"
                embed.add_field(
                    name="\u200b",
                    value=f"**{admin_name}** - *{admin_title}*",
                    inline=False
                )

        await ctx.respond(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Команда на кулдауне. Попробуйте снова через {round(error.retry_after, 2)} сек.", ephemeral=True)
        else:
            raise error

def setup(client):
    client.add_cog(PlayerListCog(client))
