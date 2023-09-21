from discord import message
from discord.member import Member
from redbot.core import checks, Config, utils
from redbot.core.i18n import Translator, cog_i18n
import discord
from discord.ext import tasks
from redbot.core import commands
from redbot.core.utils import mod
import string
import random
from .game import Game, reactions, nums
from .elo import calcElo

class ConnectFour(commands.Cog):
    """Connect Four Game"""

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        default_member = {
            "elo": 1000,
            "wins": 0,
            "losses": 0,
            "ties": 0
        }
        
        self.config = Config.get_conf(self, identifier=457758648593)
        self.config.register_member(**default_member)
        self.config.register_guild(users = [])
        self.activeGames = {}
        self.gameMsgs = {}
        self.timeStatus = False

    def cog_unload(self):
        self._timer.cancel()

    @tasks.loop(seconds = 1.0)
    async def _timer(self):
        active = False
        try:
            for code in self.activeGames:
                game : Game = self.activeGames[code]
                if game.status == 1:
                    active = True
                    if game.time > 0:
                        game.time -= 1
                    else:
                        if game.free_cells < game.width * (game.height - 1) - 1:
                            game.status = 5
                            game.winner = 1 - game.current_player
                        else:
                            await self._abort(game.message, game.players[game.current_player], game)
                            continue
                            # early abort
                    await self._draw(game)
        except:
            return
        
        if not active:
            self.timeStatus = False
            self._timer.stop()
            print("timer stopped")

                

    async def _sendMsg(self, ctx, user, title, msg, dm = False, delete_timer=None):
        data = discord.Embed(colour=discord.Color.dark_blue())
        data.add_field(name = title, value=msg)
        if not dm:
            await ctx.send(embed=data, delete_after = delete_timer)
        else:
            await user.send(embed=data, delete_after = delete_timer)

    @commands.group(name="c4")
    @commands.guild_only()
    async def c4(self, ctx):
        """Connect 4"""
        pass        

    @c4.command(pass_context=True)
    @commands.guild_only()   
    async def start(self, ctx, turn_timer=60):
        """
        Start a new game, accepts optional turn time
        Use c4 start <time>, for example, if = is your prefix, =c4 start 50 starts a game with 50 seconds per turn.
        """
        for game in self.activeGames:
            if ctx.author in self.activeGames[game].players:
                await self._sendMsg(ctx, None, "Error", f"You are already in a [game]({self.activeGames[game].message.jump_url}), finish or cancel it before starting another!")
                return

        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            if code not in self.activeGames:
                break
        
        users = await self.config.guild(ctx.guild).users()
        if ctx.author.id not in users:
            users.append(ctx.author.id)
            await self.config.guild(ctx.guild).users.set(users)

        elo = await self.config.member(ctx.author).elo()

        new_game = Game(code, turn_timer)
        new_game.join(ctx.author, elo)
        self.activeGames[code] = new_game
        content = discord.Embed(colour=discord.Color.dark_blue(), title = f'*Connect 4*', description = f'Started by: `{ctx.author.display_name} ({elo})`\nTime per turn: `{turn_timer} seconds`')
        content.add_field(name = new_game.getStatus(), value = new_game.draw())
        prefix = await self.bot.command_prefix(self.bot, ctx)
        content.set_footer(text = f'Click ✅ or type "{prefix[0]}c4 join {code}" to join this game.')
        game_msg = await ctx.send(embed = content)
        new_game.message = game_msg
        self.gameMsgs[game_msg] = new_game

        await game_msg.add_reaction("✅")
        await game_msg.add_reaction("❎")

    @c4.command(pass_context=True)
    @commands.guild_only()   
    async def join(self, ctx, code):
        """Join an existing game"""
        code = code.upper()
        if code not in self.activeGames:
            await self._sendMsg(ctx, None, "Unable to join game", f"<@{ctx.author.id}> Invalid join code!")
            return

        game : Game = self.activeGames[code]

        if ctx.author in game.players:
            await self._sendMsg(ctx, None, "Unable to join game", f"<@{ctx.author.id}> You are already in the game!")
            return        

        if game.status > 0:
            await self._sendMsg(ctx, None, "Unable to join game", f"<@{ctx.author.id}> Game in progress!")
            return           
            
        await self._join(game.message, ctx.author, game)
        
    @c4.command(pass_context=True)
    @commands.guild_only()   
    async def games(self, ctx):
        """Displays a list of all active games"""
        gamelist = f'`{"PLAYER 1":20}{"PLAYER 2":20}{"STATUS":22}`\n'
        for code in self.activeGames:
            game = self.activeGames[code]
            gamelist += f'`{game.players[0].display_name[:19]:20}{game.players[1].display_name[:19] if game.status > 0 else "-":20}{game.getStatus()[:21]:22}` [({game.code})]({game.message.jump_url})\n'
        #gamelist += ' ```'

        content = discord.Embed(colour=discord.Color.blurple())
        content.add_field(name = f'{len(self.activeGames)} Active Game(s)', value = gamelist)
        prefix = await self.bot.command_prefix(self.bot, ctx)
        content.set_footer(text = f'Type "{prefix[0]}c4 join [code]" to join a game.')

        await ctx.send(embed = content)


    @c4.command(pass_context=True)
    @commands.guild_only()   
    async def stat(self, ctx, user : discord.Member = None):
        """Displays a list of all active games"""
        if not user:
            user = ctx.author

        content = discord.Embed(colour=discord.Color.blurple(), title = user.display_name)
        content.set_thumbnail(url=user.avatar.url)
        data = await self.config.member(user).get_raw()
        for k, v in data.items():
            content.add_field(name = k.upper(), value = v)
        content.add_field(name = "GAMES PLAYED", value = data['wins'] + data['losses'] + data['ties'])
        await ctx.send(embed = content)

    @c4.command(pass_context=True)
    @commands.guild_only()   
    async def leader(self, ctx):
        """Displays the leaderboard"""

        
        users = await self.config.guild(ctx.guild).users()
        ranked = []

        for uid in users:
            user = ctx.guild.get_member(uid)
            if user:
                elo = await self.config.member(user).elo()
                ranked.append((elo, user))
        ranked.sort(key = lambda x: x[0] ,reverse=True)

        leaderboard = f'`{"#":2} {"NAME":15} {"ELO":5} {"WIN":4} {"LOSS":4} TOTAL`\n'
        count = 0
        for elo, user in ranked:
            count += 1
            data = await self.config.member(user).get_raw()
            leaderboard += f'`{count:<2d} {user.display_name[:15]:15} {elo:<5d} {data["wins"]:4d} {data["losses"]: 4d} {data["wins"] + data["losses"] + data["ties"]: 5d}`\n'
            if count == 20:
                break
        
        content = discord.Embed(colour=discord.Color.blurple(), title = 'Connect 4 Leaderboard', description = leaderboard)
        await ctx.send(embed = content)


    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user):
        if user.bot:
            return

        msg = reaction.message
        if msg in self.gameMsgs:
            game : Game = self.gameMsgs[msg]
            if game.status == 0:     # waiting for opponent
                if reaction.emoji == "❎" and user == game.players[0]:
                                          # cancel game
                    await self._abort(game.message, user, game)
                elif reaction.emoji == "✅" and user != game.players[0]:
                    await self._join(msg, user, game)               # player joined
                await reaction.remove(user)
            elif game.status == 1:
                if user == game.players[game.current_player] and reaction.emoji in reactions:
                    game.play(game.current_player, reactions[reaction.emoji]-1)         # PLAY MOVE
                    game.time = game.max_time

                    await self._draw(game)
                    await reaction.remove(user)
                elif user in game.players and reaction.emoji == "❎":
                    game.winner = 0 if user == game.players[1] else 1
                    game.status = 4         # forfeited
                    await self._draw(game)
                else:
                    await reaction.remove(user)


    async def _draw(self, game: Game):

        msg = game.message
        content = discord.Embed(colour=[discord.Color.dark_gold(), discord.Color.dark_red()][game.current_player], title = f"*Connect 4*", description = f'Players:\n🟡: `{game.players[0].display_name} ({game.elos[0]})`   🔴: `{game.players[1].display_name} ({game.elos[1]})`')
        content.add_field(name = game.getStatus(), value = game.draw(), inline = False)
        if game.winner == -1:
            content.set_footer(text = f'Current Player: {game.players[game.current_player].display_name} ' + ['🟡', '🔴'][game.current_player] + f'\nTurn Timer: {str(game.time // 60).zfill(2)}:{str(game.time % 60).zfill(2)}')
            #content.add_field(name = 'Current player:', value = f' **<@{game.players[game.current_player].id}>** ' + ['🟡', '🔴'][game.current_player], inline = False)
        else:
            if game.winner < 2:
                content.add_field(name = '🌟🌟 Winner: 🌟🌟', value = f' **<@{game.players[game.winner].id}>** ' + ['🟡', '🔴'][game.winner], inline = False)
            winner = game.winner
            if winner == 2:
                winner = 0.5
            new_elos = calcElo(game.elos[0], game.elos[1], 100, winner)
            content.add_field(name = 'Score Changes:', value = f'`{game.players[0].display_name}: ({game.elos[0]}) --> ({new_elos[0]})`\n`{game.players[1].display_name}: ({game.elos[1]}) --> ({new_elos[1]})`', inline = False)
            await self._updateStats(game.players, new_elos, winner)
            await msg.clear_reactions()
            self.activeGames.pop(game.code)
            self.gameMsgs.pop(msg)

        await msg.edit(embed = content)

    async def _updateStats(self, players, elos, winner):
        await self.config.member(players[0]).elo.set(elos[0])
        await self.config.member(players[1]).elo.set(elos[1])
        if winner != 0.5:
            wins = await self.config.member(players[winner]).wins()
            losses = await self.config.member(players[1 - winner]).losses()
            await self.config.member(players[winner]).wins.set(wins + 1)
            await self.config.member(players[1 - winner]).losses.set(losses + 1)
        else:
            ties0 = await self.config.member(players[0]).ties()
            ties1 = await self.config.member(players[1]).ties()
            await self.config.member(players[0]).ties.set(ties0 + 1)
            await self.config.member(players[1]).ties.set(ties1 + 1)      

    async def _join(self, msg : discord.Message, user : discord.Member, game):
        users = await self.config.guild(msg.guild).users()                      # add player to active players if not already on the list
        if user.id not in users:
            users.append(user.id)
            await self.config.guild(msg.guild).users.set(users)
        elo = await self.config.member(user).elo()

        for id, game in self.activeGames.items():
            if user in game.players:
                await self._sendMsg(msg.channel, None, "Error", f"{user.mention} You are already in a [game]({self.activeGames[id].message.jump_url}), finish or cancel it before starting another!", False, 5)
                return

        game.join(user, elo)                                                     # new player joins!

        content = discord.Embed(colour=discord.Color.blurple(), title = '🎲 Game starting... 🎲', description = f'{user.mention} has joined the [game]({msg.jump_url}) started by {game.players[0].mention}')
        await msg.channel.send(embed = content, delete_after = 20)
        
        await self._draw(game)
        await msg.clear_reactions()

        for i in range(1, 8):
            await msg.add_reaction(nums[i])
        await msg.add_reaction('❎')
        
        if not self.timeStatus:
            self.timeStatus = True
            self._timer.start()
            print("timer started")

    async def _abort(self, msg, user, game):      
        self.activeGames.pop(game.code)
        self.gameMsgs.pop(msg)
        game.status = 5              
        await msg.clear_reactions()
        await msg.edit(embed = discord.Embed(colour=discord.Color.dark_blue(), title = "Connect 4", description = f"Cancelled by **{user.display_name}**"))