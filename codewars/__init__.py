from .main import Codewars


async def setup(bot):
    bot.add_cog(Codewars(bot))
