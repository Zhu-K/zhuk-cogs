from .autoinactive import AutoInactive

def setup(bot):
    #checkinactive = AutoInactive(bot)
    bot.add_cog(AutoInactive(bot))
    #bot.loop.create_task(checkinactive._checkInactivity())