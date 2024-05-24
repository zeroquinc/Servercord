import discord

class EmbedBuilder:
    def __init__(self, title='', description='', color=discord.Color.default()):
        self.embed = discord.Embed(title=title, description=description, color=color)

    def set_author(self, name, icon_url=None, url=None):
        self.embed.set_author(name=name, icon_url=icon_url, url=url)
        return self

    def add_field(self, name, value, inline=True):
        self.embed.add_field(name=name, value=value, inline=inline)
        return self

    def set_footer(self, text, icon_url=None):
        self.embed.set_footer(text=text, icon_url=icon_url)
        return self
    
    def set_thumbnail(self, url):
        self.embed.set_thumbnail(url=url)
        return self

    def build(self):
        return self.embed
    
    async def send_embed(self, channel):
        # Send the embed to the specified channel
        await channel.send(embed=self.build())