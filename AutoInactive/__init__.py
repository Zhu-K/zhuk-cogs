from .autoinactive import AutoInactive

def async setup(bot):
    await bot.add_cog(AutoInactive(bot))
