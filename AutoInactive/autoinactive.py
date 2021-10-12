from redbot.core import Config
import discord
from discord.ext import tasks
from redbot.core import commands
import datetime
import time


class AutoInactive(commands.Cog):
    """The Automatic Inactivity Role Assigner Cog"""
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.DEFAULT_WARNING = "Just a friendly reminder that you have been inactive in {guildname} for {days} days. Our server assigns an inactive status after {maxdays} days of inactivity. Come say hi!"
        self.DEFAULT_MSG = "You have been assigned the inactive role due to inactivity after {maxdays} days."
        default_guild = {
            "active_list": [],
            "warning_days" : 30, 
            "inactivity_days" : 60,
            "inactive_msg": self.DEFAULT_MSG,
            "warning_msg": self.DEFAULT_WARNING,
            "inactive_role": None
        }
        self.config = Config.get_conf(self, identifier=457758648554)
        self.config.register_guild(**default_guild)
        self.config.register_member(warned = False, last_active = None)
        self.config.register_global(active_guilds = [])
        # write to database in chunks to reduce accesses
        self.last_write = 0
        self.buffer = set()
        self.write_delay = 600  # write buffer to config every 10 minutes
        print("Starting inactivity check loop...")
        self._checkInactivity.start()
    
    def cog_unload(self):
        self._checkInactivity.cancel()

    # monitor messages to update buffer for activity
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
            inactivity_days = await self.config.guild(guild).inactivity_days()
            warning_days = await self.config.guild(guild).warning_days()

            inactive_msg = await self.config.guild(guild).inactive_msg()
            warning_msg = await self.config.guild(guild).warning_msg()
            new_active_list = []
            print("checking " + str(len(active_list))+ " members...")
            for uid in active_list:
                user = guild.get_member(uid)
                if not user:
                    print(str(uid) + ' does not point to a valid user!')
                    continue
                warned = await self.config.member(user).warned()
                last_active = await self.config.member(user).last_active()
                last_active = datetime.datetime.strptime(last_active,"%Y-%m-%d").date()
                days_since = (datetime.date.today() - last_active).days
                if days_since > inactivity_days:
                    # await self._sendMsg(None, user, "Inactivity Notice", inactive_msg.format(guildname = guild.name, days = days_since, maxdays = inactivity_days), dm=True)
                    # await user.add_roles(role)
                    print(user.name + " has been assigned to inactive role")
                else:
                    new_active_list.append(uid)
                    if days_since > warning_days and not warned:
                        # await self.config.member(user).warned.set(True)
                        # await self._sendMsg(None, user, "Inactivity Reminder", warning_msg.format(guildname = guild.name, days = days_since, maxdays = inactivity_days), dm=True)
                        print(user.name + " has been sent an inactivity warning")
                    else:
                        if warned:                          # active again, remove warned tag
                            await self.config.member(user).warned.set(False)
            await self.config.guild(guild).active_list.set(new_active_list)

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
        """Start inactivity monitoring on current server"""
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

 
    @inact.command(pass_context=True)
    @commands.guild_only()
    async def scan(self, ctx, check = False):
        """
        Start a serverwide scan for most recent activities
        Used for populating the server active user list
        Optional parameter [check] will assign inactive roles immediately when set to True, default False mode waits for next scheduled activity check.
        """
        role = await self.config.guild(ctx.guild).inactive_role()
        role = discord.utils.get(ctx.guild.roles, id=role)
        if not role:
            await self._sendMsg(ctx, ctx.author, "Error", "Inactive role not set! Set inactive role before using this feature")
            return

        await self._sendMsg(ctx, ctx.author, "In progress", "Scanning message history for inactivity, this may take some time...")
        inactivity_days = await self.config.guild(ctx.guild).inactivity_days()
        no_activity = datetime.datetime.now() - datetime.timedelta(days = 5000)
        cutoff = datetime.datetime.now() - datetime.timedelta(days = inactivity_days)

        user_activity = {}                                    # dict of user : most recent activity time
        active_list = []

        for user in ctx.guild.members:
            if not user.bot and role not in user.roles:     # not bot and not already inactive
                user_activity[user.id] = no_activity
                active_list.append(user.id)
            await self.config.guild(ctx.guild).active_list.set(active_list)

        for channel in ctx.guild.text_channels:
            async for message in channel.history(after = cutoff, oldest_first = False):
                if message.author.id in user_activity:
                    print(channel.name, message.created_at, message.author, message.clean_Content)
                    if message.created_at > user_activity[message.author.id]:
                        user_activity[message.author.id] = message.created_at
    
        for uid, last_active in user_activity.items():
            user = ctx.guild.get_member(uid)
            await self.config.member(user).last_active.set(str(last_active.date()))

        if check:
            await self._checkInactivity()
            active_list = await self.config.guild(ctx.guild).active_list()
            await self._sendMsg(ctx, ctx.author, "Successful", f"Scanning complete. There are currently {len(active_list)} active users on this server.")
        else:
            await self._sendMsg(ctx, ctx.author, "Successful", "Scanning complete. Most recent activities of all users have been scanned")

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
    async def checknow(self, ctx):
        """Force a global inactivity check now"""
        await self._checkInactivity()
        await self._sendMsg(ctx, ctx.author, "Success", "Inactivity check complete")


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
        """
        Customize inactivity notification message
        Available pattern tags:
        -----------------------
        {days}: days since user's last activity
        {maxdays}: max days of inactivity before role assignment
        {guildname}: name of this guild
        """
        if msg == "reset":
            await self.config.guild(ctx.guild).inactive_msg.set(self.DEFAULT_MSG)
            await self._sendMsg(ctx, ctx.author, "Reset Successful", "Inactivation notification message set to default")
        else:
            await self.config.guild(ctx.guild).inactive_msg.set(msg)
            await self._sendMsg(ctx, ctx.author, "New notification Successfully Set", msg)

    @inact.command(pass_context=True)
    @commands.guild_only()
    async def warning(self, ctx, *, msg):
        """
        Customize inactivity reminder message
        Available pattern tags:
        -----------------------
        {days}: days since user's last activity
        {maxdays}: max days of inactivity before role assignment
        {guildname}: name of this guild
        """
        if msg == "reset":
            await self.config.guild(ctx.guild).warning_msg.set(self.DEFAULT_WARNING)
            await self._sendMsg(ctx, ctx.author, "Reset Successful", "Inactivation warning message set to default")
        else:
            await self.config.guild(ctx.guild).warning_msg.set(msg)
            await self._sendMsg(ctx, ctx.author, "New Warning Successfully Set", msg)

    @inact.command(pass_context=True)
    @commands.guild_only()
    async def daysinactive(self, ctx, *, threshold):
        """Customize # of days to qualify as inactive"""
        if threshold.isnumeric() and int(threshold) > 0:
            days = int(threshold)
            await self.config.guild(ctx.guild).inactivity_days.set(days)
            await self._sendMsg(ctx, ctx.author, "Successful", "Inactivation threshold set to " + str(days) + " days.")
        else:
            await self._sendMsg(ctx, ctx.author, "Error", "Invalid threshold input. Must be integer")

    @inact.command(pass_context=True)
    @commands.guild_only()
    async def dayswarn(self, ctx, *, threshold):
        """Customize # of days before sending a warning"""
        if threshold.isnumeric() and int(threshold) > 0:
            days = int(threshold)
            await self.config.guild(ctx.guild).warning_days.set(days)
            await self._sendMsg(ctx, ctx.author, "Successful", "Warning threshold set to " + str(days) + " days.")
        else:
            await self._sendMsg(ctx, ctx.author, "Error", "Invalid threshold input. Must be integer")

    @inact.command(pass_context=True)           
    @commands.guild_only()
    async def status(self, ctx):
        """Displays a summary of AutoInactive status"""
        servers = await self.config.active_guilds()
        active_list = await self.config.guild(ctx.guild).active_list()
        inactivity_days = await self.config.guild(ctx.guild).inactivity_days()
        warning_days = await self.config.guild(ctx.guild).warning_days()
        inactive_msg = await self.config.guild(ctx.guild).inactive_msg()
        warning_msg = await self.config.guild(ctx.guild).warning_msg()
        role = await self.config.guild(ctx.guild).inactive_role()
        if role:
            role = discord.utils.get(ctx.guild.roles, id=role).name
        else:
            role = "None"
        toggle = 'On' if ctx.guild.id in servers else 'Off'
        
        fields = {
            "Server Status" : toggle,
            "Active Members" : len(active_list),
            "Max Inactivity": str(inactivity_days) + " days",
            "Warn after": str(warning_days) + " days",
            "Inactivity Notification": inactive_msg,
            "Inactivity Warning": warning_msg,
            "Inactive Role" : role
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
            await self.config.member(user).warned.set(False)
            await self.config.member(user).last_active.set(str(datetime.date.today()))
            await user.remove_roles(role)
        else:
            await self._sendMsg(ctx, user, "Error", "There is nothing to reactivate, you are not marked as inactive!", dm=True)