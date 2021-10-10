from redbot.core import checks, Config, utils
from redbot.core.i18n import Translator, cog_i18n
import discord
from discord.ext import tasks
from redbot.core import commands
from redbot.core.utils import mod
import asyncio
import datetime
import time


class AutoInactive(commands.Cog):
    """The Automatic Inactivity Role Assigner Cog"""

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.DEFAULT_MSG = "BAM YOU GOT MOVED FOR INACTIVITY!!!!11"
        default_guild = {
            "active_list": [],
            "threshold_days": 20,
            "msg": self.DEFAULT_MSG,
            "inactive_role": None
        }
        self.config = Config.get_conf(self, identifier=457758648554)
        self.config.register_guild(**default_guild)
        self.config.register_member(last_active = None)
        self.config.register_global(active_guilds = [])
        # write to database in chunks to reduce accesses
        self.last_write = 0
        self.buffer = set()
        self.write_delay = 600  # write buffer to config every 10 minutes
        print("attempting to start inactivity check loop")
        self._checkInactivity.start()
    
    def cog_unload(self):
        self._checkInactivity.cancel()

    @commands.Cog.listener()
    async def on_message(self, ctx):
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
        if not self.buffer:
            return
        active_list = await self.config.guild(ctx.guild).active_list()
        role = await self.config.guild(ctx.guild).inactive_role()
        role = discord.utils.get(ctx.guild.roles, id=role)
        active_set = set(active_list)
        for user in self.buffer:
            if user.id not in active_set and role not in user.roles:             
                active_list.append(user.id)
            await self.config.member(user).last_active.set(str(datetime.date.today()))
        await self.config.guild(ctx.guild).active_list.set(active_list)

    @tasks.loop(hours = 24.0) 
    async def _checkInactivity(self):
        #while True:
        print("starting inactivity check")
        active_guilds = await self.config.active_guilds()
        for gid in active_guilds:
            guild = self.bot.get_guild(gid)
            print("checking guild", gid, guild.name)
            role = await self.config.guild(guild).inactive_role()
            role = discord.utils.get(guild.roles, id=role)
            if not role:
                print("Inactive role not set, skipping inactivity check for " + guild.name)
                continue

            active_list = await self.config.guild(guild).active_list()
            threshold_days = await self.config.guild(guild).threshold_days()
            threshold_date = datetime.date.today() - datetime.timedelta(days = threshold_days)
            msg = await self.config.guild(guild).msg()
            new_active_list = []
            print("checking " + str(len(active_list))+ " members...")
            for uid in active_list:
                user = guild.get_member(uid)
                if not user:
                    print(str(uid) + 'does not point to a valid user!')
                    continue
                last_active = await self.config.member(user).last_active()
                last_active = datetime.datetime.strptime(last_active,"%Y-%m-%d").date()
                if last_active < threshold_date:
                    await self._sendMsg(None, user, "Inactivity Notice", msg, dm=True)
                    await user.add_roles(role)
                else:
                    new_active_list.append(uid)
            await self.config.guild(guild).active_list.set(new_active_list)
            #await asyncio.sleep(86400)   

    @_checkInactivity.before_loop
    async def before_checkInactivity(self):
        await self.bot.wait_until_red_ready()

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

    @inact.command(pass_context=True)
    @commands.guild_only()
    async def on(self, ctx):
        """Starts inactivity monitoring on current server"""
        role = await self.config.guild(ctx.guild).inactive_role()
        if not role:
            await self._sendMsg(ctx, ctx.author, "Error", "Inactive role not set! Set inactive role before turning this feature on")
            return

        active_guilds = await self.config.active_guilds()
        if ctx.guild.id in active_guilds:
            await self._sendMsg(ctx, ctx.author, "Error", "Automatic Inactivation already set to on for this server!")
        else:
            active_guilds.append(ctx.guild.id)
            await self._sendMsg(ctx, ctx.author, "Success", "Automatic Inactivation set to on for this server!")
            await self.config.active_guilds.set(active_guilds)

            active_list = []
            role = discord.utils.get(ctx.guild.roles, id=role)

            for user in ctx.guild.members:
                if user.bot:
                    continue
                if role not in user.roles:
                    active_list.append(user.id)
                    last_active = await self.config.member(user).last_active()
                    if not last_active:
                        await self.config.member(user).last_active.set(str(datetime.date.today()))
            
            await self.config.guild(ctx.guild).active_list.set(active_list)
 
    @inact.command(pass_context=True)
    @commands.guild_only()   
    async def off(self, ctx):
        """Stops inactivity monitoring on current server"""
        active_guilds = await self.config.active_guilds()
        if ctx.guild.id in active_guilds:
            active_guilds.remove(ctx.guild.id)
            await self.config.active_guilds.set(active_guilds)
            await self._sendMsg(ctx, ctx.author, "Success", "Automatic Inactivation set to off for this server!")
        else:
            await self._sendMsg(ctx, ctx.author, "Error", "Automatic Inactivation already set to off for this server!")

    @inact.command(pass_context=True)
    @commands.guild_only()
    async def role(self, ctx, *, role_name):
        """Assign inactive members to existing role"""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            await self.config.guild(ctx.guild).inactive_role.set(role.id)
            await self._sendMsg(ctx, ctx.author, "Success", "Inactive role set to " + str(role))
        else:
            await self.config.guild(ctx.guild).inactive_role.set(None)
            await self._sendMsg(ctx, ctx.author, "Error", role_name + " is not a valid role!")

    @inact.command(pass_context=True)
    @commands.guild_only()
    async def msg(self, ctx, *, msg):
        """Customize inactivity notification message"""
        if msg == "reset":
            await self.config.guild(ctx.guild).msg.set(self.DEFAULT_MSG)
            await self._sendMsg(ctx, ctx.author, "Reset Successful", "Inactivation notification message set to default")
        else:
            await self.config.guild(ctx.guild).msg.set(msg)
            await self._sendMsg(ctx, ctx.author, "New notification Successfully Set", msg)

    @inact.command(pass_context=True)
    @commands.guild_only()
    async def days(self, ctx, *, threshold):
        """Customize # of days to qualify as inactive"""
        if threshold.isnumeric() and int(threshold) > 0:
            days = int(threshold)
            await self.config.guild(ctx.guild).threshold_days.set(days)
            await self._sendMsg(ctx, ctx.author, "Successful", "Inactivation threshold set to " + str(days) + " days.")
        else:
            await self._sendMsg(ctx, ctx.author, "Error", "Invalid threshold input. Must be integer")
    
    @inact.command(pass_context=True)           
    @commands.guild_only()
    async def status(self, ctx):
        """Displays a summary of AutoInactive status"""
        servers = await self.config.active_guilds()
        active_list = await self.config.guild(ctx.guild).active_list()
        days = await self.config.guild(ctx.guild).threshold_days()
        msg = await self.config.guild(ctx.guild).msg()
        role = await self.config.guild(ctx.guild).inactive_role()
        role = discord.utils.get(ctx.guild.roles, id=role)
        toggle = 'On' if ctx.guild.id in servers else 'Off'
        
        fields = {
            "Server Status" : toggle,
            "Active Members" : len(active_list),
            "Max Inactivity": str(days) + " days",
            "Notification Text": msg,
            "Inactive Role" : role.name
        }
        data = discord.Embed(colour=ctx.author.colour)
        for k, v in fields.items():
            data.add_field(name=k, value=v)
        await ctx.send(embed=data)

    @commands.command(name="inactivate")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def inactivate(self, ctx, user: discord.Member, delayed = None):
        """Override to set someone inactive"""
        await self.config.member(user).last_active.set(str(datetime.date.today()-datetime.timedelta(days = 500)))
        active_list = await self.config.guild(ctx.guild).active_list()
        if user.id not in active_list:
            active_list.append(user.id)
            await self.config.guild(ctx.guild).active_list.set(active_list)
        if not delayed:
            await self._checkInactivity()
        await self._sendMsg(ctx, ctx.author, "Successful", user.name + " has been set to inactive.")

    @commands.command(name="reactivate")
    @commands.guild_only()
    async def reactivate(self, ctx):
        """reactivate an inactive account"""
        print("reactivation request from " + ctx.author.name)
        role = await self.config.guild(ctx.guild).inactive_role()
        role = discord.utils.get(ctx.guild.roles, id=role)
        user = ctx.author
        if not role:
            return
        if role in user.roles:
            await self._sendMsg(ctx, user, "Reactivation Successful", "Congratulations, you have been reactivated!", dm=True)
            active_list = await self.config.guild(ctx.guild).active_list()
            active_list.append(user.id)
            await self.config.guild(ctx.guild).active_list.set(active_list)
            await self.config.member(user).last_active.set(str(datetime.date.today()))
            await user.remove_roles(role)
        else:
            await self._sendMsg(ctx, user, "Error", "There is nothing to reactivate, you are not marked as inactive!", dm=True)