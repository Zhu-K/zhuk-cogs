from .mancala import Mancala

def setup(bot):
    bot.add_cog(Mancala(bot))