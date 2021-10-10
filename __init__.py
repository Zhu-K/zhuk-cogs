from .autoinactive import AutoInactive

def setup(bot):
    bot.add_cog(AutoInactive(bot))