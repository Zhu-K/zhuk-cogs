from redbot.core import checks, Config, utils
from redbot.core.i18n import Translator, cog_i18n
import discord
from discord.ext import tasks
from redbot.core import commands
from redbot.core.utils import mod
import asyncio
import datetime
import time


class Mancala(commands.Cog):
    """The Automatic Inactivity Role Assigner Cog"""

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        default_member = {
            "ELO": 1000,
            "Wins": 0,
            "Losses": 0
        }
        self.config = Config.get_conf(self, identifier=457758648553)
        self.config.register_member(default_member)

    async def _sendMsg(self, ctx, user, title, msg, dm = False):
        data = discord.Embed(colour=user.colour)
        data.add_field(name = title, value=msg)
        if not dm:
            await ctx.send(embed=data)
        else:
            await user.send(embed=data)

    @commands.group(name="inact")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def inact(self, ctx):
        """Configure inactive role assignment"""
        pass        