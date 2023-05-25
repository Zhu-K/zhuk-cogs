from .autoinactive import AutoInactive

async def setup(bot):
    await bot.add_cog(AutoInactive(bot))
