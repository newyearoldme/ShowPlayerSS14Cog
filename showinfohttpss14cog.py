import discord
from discord.ext import commands
from utils.config_loader import load_online_bots_config

if "cogs" in __name__:
    from .HTTPrequest import fetch_player_list, fetch_admin_players
else:
    from HTTPrequest import fetch_player_list, fetch_admin_players


class PaginatedView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__()
        self.embeds = embeds
        self.current_page = 0
        self.message: discord.WebhookMessage | None = None
        self.update_buttons()

    def update_buttons(self):
        """Обновляет состояние кнопок в зависимости от текущей страницы"""
        self.first_page.disabled = self.current_page == 0
        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == len(self.embeds) - 1
        self.last_page.disabled = self.current_page == len(self.embeds) - 1

    async def on_timeout(self):
        """Прекращает работу после таймаута"""
        for button in self.children:
            button.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except discord.NotFound:
            pass

    @discord.ui.button(label="⏪", style=discord.ButtonStyle.secondary)
    async def first_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = 0
        self.update_buttons()
        await self.update_embed(interaction)

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def previous_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await self.update_embed(interaction)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = min(len(self.embeds) - 1, self.current_page + 1)
        self.update_buttons()
        await self.update_embed(interaction)

    @discord.ui.button(label="⏩", style=discord.ButtonStyle.secondary)
    async def last_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = len(self.embeds) - 1
        self.update_buttons()
        await self.update_embed(interaction)

    @discord.ui.button(label="❌", style=discord.ButtonStyle.red)
    async def stop(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Останавливает пагинацию (удаляет сообщение)"""
        if self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass
            self.message = None
        self.clear_items()

    async def update_embed(self, interaction: discord.Interaction):
        """Обновляет текущий Embed и состояние кнопок"""
        if self.message:
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def send(self, ctx):
        """Отправляет первое сообщение и активирует пагинацию"""
        self.update_buttons()
        self.message = await ctx.respond(embed=self.embeds[self.current_page], view=self)


class PlayerListCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.servers = load_online_bots_config("online_servers_bots.json")
        self.colors = {
            "player_list": discord.Color.blue(),
            "admin_list": discord.Color.green()
        }

    async def server_autocomplete(self, ctx: discord.AutocompleteContext):
        """Автодополнение для списка серверов."""
        return [srv.name for srv in self.servers]

    def create_embed_pages(self, title: str, items: list, color: discord.Color, footer: str) -> list:
        """Создаёт страницы с Embed"""
        embeds = []
        for i in range(0, len(items), 10):
            chunk = items[i:i + 10]
            text = "\n".join(chunk)
            if len(text) > 1024:
                text = text[:1021] + "..."
            embed = discord.Embed(title=title, color=color)
            embed.set_footer(text=footer)
            embed.add_field(
                name=f"Страница {i // 10 + 1} из {(len(items) - 1) // 10 + 1}",
                value=text,
                inline=False,
            )
            embeds.append(embed)
        return embeds

    def get_list_data(self, selected_server, list_type):
        """Получает данные для списка игроков или администраторов"""
        if list_type == "player_list":
            return fetch_player_list(selected_server)
        elif list_type == "admin_list":
            return fetch_admin_players(selected_server)
        return None

    @commands.slash_command(description="Показать список игроков или администраторов на определённом сервере")
    async def show_player_list(
        self,
        ctx: discord.ApplicationContext,
        server: str = discord.Option(description="Выберите сервер", autocomplete=server_autocomplete),
        list_type: str = discord.Option(description="Выберите тип списка", choices=["player_list", "admin_list"]),
    ):
        await ctx.defer(ephemeral=True)

        servers = {srv.name: srv for srv in self.servers}
        if server not in servers:
            await ctx.respond("Указанный сервер не найден")
            return

        selected_server = servers[server]
        result = self.get_list_data(selected_server, list_type)

        # Формирование Embed
        title = f"{'Игроки' if list_type == 'player_list' else 'Администраторы'} на сервере {selected_server.name}"
        footer = f"Всего: {len(result)}"
        items = (
            [f"{player}" for player in result]
            if list_type == "player_list"
                else [
            f"**{name}** {'[R]' if details['readmin'] else ''} - {details['title']}"
            for name, details in result.items()
            ]
        )
        embeds = self.create_embed_pages(title, items, self.colors[list_type], footer)

        if isinstance(result, dict) and "error" in result:
            await ctx.respond(f"Ошибка при запросе данных: {result['error']}")
        elif embeds:
            view = PaginatedView(embeds)
            await view.send(ctx)
        else:
            await ctx.respond(f"На сервере {selected_server.name} нет данных для выбранного списка")


def setup(client):
    client.add_cog(PlayerListCog(client))
