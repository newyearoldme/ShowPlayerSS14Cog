from .showinfohttpss14cog import PlayerListCog

def setup(client):
    client.add_cog(PlayerListCog(client))