from .connectfour import ConnectFour

def setup(bot):
    bot.add_cog(ConnectFour(bot))