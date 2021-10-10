from redbot.core import checks, Config, utils
from redbot.core.i18n import Translator, cog_i18n
import discord
from discord.ext import tasks
from redbot.core import commands
from redbot.core.utils import mod
import asyncio
import datetime
import time

### GET CHANNEL BY NAME ###
# channel = discord.utils.get(ctx.guild.channels, name=given_name)
# channel_id = channel.id

### LISTENER ###
    


class AutoInactive(commands.Cog):
    """The Automatic Inactivity Role Assigner Cog"""

    def __init__(self, bot):
        self.bot = bot
        self.DEFAULT_MSG = "BAM YOU GOT MOVED FOR INACTIVITY!!!!11"
        default_guild = {
            "active_set": set(),
            "threshold_days": 20,
            "msg": self.DEFAULT_MSG,
            "inactive_role": None
        }
        self.config = Config.get_conf(self, identifier=457758648554)
        self.config.register_guild(**default_guild)
        self.config.register_member(last_active = None)
        self.config.register_global(active_guilds = set())
        self.config.register
        # write to database in chunks to reduce accesses
        self.last_write = 0
        self.buffer = set()
        self.write_delay = 600  # write buffer to config every 10 minutes
        self._checkInactivity.start()


    @commands.Cog.listener()
    async def on_message(self, ctx):
        # Don't run under certain conditions
        if ctx.author.bot:
            return

        user = ctx.author
        if user not in self.buffer:
            self.buffer.add(user)

        if time.time() - self.last_write > self.write_delay:
            await self._writeBuffer(ctx)
            self.buffer.clear()
            self.last_write = time.time()
            
    async def _writeBuffer(self, ctx):
        active_set = await self.config.guild(ctx.guild).active_set()

        for user in self.buffer:
            await self.config.member(user).last_active.set(datetime.date.today())

        await self.config.guild(ctx.guild).active_set.set(active_set)

    @tasks.loop(seconds=30.0)   # change to 7 days after testing
    async def _checkInactivity(self):
        active_guilds = await self.config.GLOBAL.active_guilds()
        for guild in active_guilds:
            role = await self.config.guild(guild).inactive_role()
            if not role:
                print("Inactive role not set, skipping inactivity check for " + guild.name)
                continue

            active_set = await self.config.guild(guild).active_set()
            threshold_days = await self.config.guild(guild).threshold_days()
            threshold_date = datetime.date.today() - datetime.timedelta(days = threshold_days)
            msg = await self.config.guild(guild).msg()
            
            for user in active_set:
                last_active = await self.config.member(user).last_active()
                if last_active < threshold_date:
                    active_set.remove(user)
                    await self._sendMsg(None, user, "Inactivity Notice", msg, dm=True)
                    await self.bot.add_roles(user, [role])

            await self.config.guild(guild).active_set.set(active_set)


    async def _sendMsg(self, ctx, user, title, msg, dm = False):
        data = discord.Embed(colour=user.colour)
        data.add_field(name = title, value=msg)
        if not dm:
            await ctx.send(embed=data)
        else:
            await user.send(embed=data)

    @commands.command(name="reactivate")
    @commands.guild_only()
    async def reactivate(self, ctx):
        """reactivate an inactive account"""
        active_guilds = await self.config.GLOBAL.active_guilds()
        if ctx.guild not in active_guilds:
            return
        role = self.config.guild(ctx.guild).inactive_role()
        user = ctx.author
        if role in user.roles:
            await self._sendMsg(ctx, user, "Reactivation Successful", "Congratulations, you have been reactivated!", dm=True)
            active_set = await self.config.guild(ctx.guild).active_set()
            active_set.add(user)
            await self.config.guild(ctx.guild).active_set.set(active_set)
            await self.config.member(user).last_active.set(datetime.date.today())


    @commands.group(name="autoinactive")
    @commands.guild_only()
    #@commands.is_owner()
    async def autoinactive(self, ctx):
        """Configure inactive role assignment"""
        pass        

    @autoinactive.command(pass_context=True)
    @commands.guild_only()
    async def on(self, ctx):
        """Starts inactivity monitoring on current server"""
        role = await self.config.guild(ctx.guild).inactive_role()
        if not role:
            await self._sendMsg(ctx, ctx.author, "Error", "Inactive role not set! Set inactive role before turning this feature on")
            return
        active_guilds = await self.config.GLOBAL.active_guilds()
        if ctx.guild in active_guilds:
            await self._sendMsg(ctx, ctx.author, "Error", "Automatic Inactivation already set to on for this server!")
        else:
            active_guilds.add(ctx.guild)
            await self._sendMsg(ctx, ctx.author, "Success", "Automatic Inactivation set to on for this server!")
            await self.config.GLOBAL.active_guilds.set(active_guilds)

 
    @autoinactive.command(pass_context=True)
    @commands.guild_only()   
    async def off(self, ctx):
        """Stops inactivity monitoring on current server"""
        active_guilds = await self.config.GLOBAL.active_guilds()
        if ctx.guild in active_guilds:
            active_guilds.remove(ctx.guild)
            await self.config.GLOBAL.active_guilds.set(active_guilds)
            await self._sendMsg(ctx, ctx.author, "Success", "Automatic Inactivation set to off for this server!")
        else:
            await self._sendMsg(ctx, ctx.author, "Error", "Automatic Inactivation already set to off for this server!")

    @autoinactive.command(pass_context=True)
    @commands.guild_only()
    async def role(self, ctx, *, role_name):
        """Assign inactive members to existing role"""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            await self.config.guild(ctx.guild).inactive_role.set(role[0])
            await self._sendMsg(ctx, ctx.author, "Success", "Inactive role set to " + role[0])
        else:
            await self.config.guild(ctx.guild).inactive_role.set(None)
            await self._sendMsg(ctx, ctx.author, "Error", role_name + "is not a valid role!")

    @autoinactive.command(pass_context=True)
    @commands.guild_only()
    async def msg(self, ctx, *, msg):
        """Customize inactivity notification message"""
        if msg == "reset":
            await self.config.guild(ctx.guild).msg.set(self.DEFAULT_MSG)
            await self._sendMsg(ctx, ctx.author, "Reset Successful", "Inactivation notification message set to default")
        else:
            await self.config.guild(ctx.guild).msg.set(msg)
            await self._sendMsg(ctx, ctx.author, "New notification Successfully Set", msg)

    @autoinactive.command(pass_context=True)
    @commands.guild_only()
    async def days(self, ctx, *, threshold):
        """Customize # of days to qualify as inactive"""
        if threshold.isnumeric() and threshold > 0:
            days = int(threshold)
            await self.config.guild(ctx.guild).threshold_days.set(days)
            await self._sendMsg(ctx, ctx.author, "Successful", "Inactivation threshold set to " + str(days) + " days.")
        else:
            await self._sendMsg(ctx, ctx.author, "Error", "Invalid threshold input. Must be integer")

    @autoinactive.command(pass_context=True)
    @commands.guild_only()
    async def inactivate(self, ctx, *, user: discord.Member):
        """test function to make someone inactive"""
        await self.config.member(user).last_active.set(datetime.date.today()-datetime.timedelta(days = 500))
        await self._sendMsg(ctx, ctx.author, "DEBUG", "inactivated " + user.name)
        

