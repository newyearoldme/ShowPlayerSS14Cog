import discord
from discord.ext import commands
from utils.config_loader import load_online_bots_config

if "cogs" in __name__:
    from .HTTPrequest import fetch_player_list, fetch_admin_players
else:
    from HTTPrequest import fetch_player_list, fetch_admin_players


class PaginatedView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__()
        self.embeds = embeds
        self.current_page = 0
        self.message = None

    async def on_timeout(self):
        """Прекращаем работу после того, как прошло достаточно времени."""
        for button in self.children:
            button.disabled = True
        if self.message:  # Проверяем, что сообщение существует
            await self.message.edit(view=self)

    @discord.ui.button(label="⏪", style=discord.ButtonStyle.secondary)
    async def first_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = 0
        await self.update_embed(interaction)

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def previous_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = max(0, self.current_page - 1)
        await self.update_embed(interaction)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = min(len(self.embeds) - 1, self.current_page + 1)
        await self.update_embed(interaction)

    @discord.ui.button(label="⏩", style=discord.ButtonStyle.secondary)
    async def last_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = len(self.embeds) - 1
        await self.update_embed(interaction)

    @discord.ui.button(label="❌", style=discord.ButtonStyle.red)
    async def stop(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Кнопка для завершения работы с пагинацией (удаляет сообщение)."""
        if self.message:
            await self.message.delete()  # Удаляем сообщение
            self.clear_items() # Останавливаем пагинацию

    async def update_embed(self, interaction: discord.Interaction):
        """Обновляем embed для отображения текущей страницы."""
        if self.message:  # Проверяем, что сообщение существует
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def send(self, ctx):
        """Отправляем первое сообщение и начнем пагинацию."""
        self.message = await ctx.respond(embed=self.embeds[self.current_page], view=self)

class PlayerListCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.servers = load_online_bots_config("online_servers_bots.json")

    # Автодополнение для сервера
    async def server_autocomplete(self, ctx: discord.AutocompleteContext):
        return [srv.name for srv in self.servers]

    @commands.slash_command(description="Получить список игроков или администраторов")
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

        # Разделение на страницы
        embeds = []
        if list_type == "player_list":
            players = result
            pages = [f"**{player}**" for player in players]
        else:  # list_type == "admin_list"
            admins = result
            pages = [f"**{admin_name}** - *{details if isinstance(details, str) else 'Без титула'}*" for admin_name, details in admins.items()]

        # Разбиваем на страницы, если слишком много данных
        for i in range(0, len(pages), 10):
            embed_page = discord.Embed(title=title, description=description, color=color)
            embed_page.set_footer(text=f"IP сервера: {selected_server.ip}")
            embed_page.add_field(name=f"**Страница {i // 10 + 1} / {(len(pages) - 1) // 10 + 1}**", value="\n".join(pages[i:i + 10]), inline=False)
            embeds.append(embed_page)

        if embeds:
            view = PaginatedView(embeds)
            await view.send(ctx)
        else:
            await ctx.respond(f"На сервере **{selected_server.name}** нет данных для выбранного типа списка", ephemeral=True)

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(f"Команда на кулдауне. Попробуйте снова через {round(error.retry_after, 2)} сек.", ephemeral=True)
        else:
            raise error

def setup(client):
    client.add_cog(PlayerListCog(client))
