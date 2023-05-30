from .main import EGS


async def setup(bot):
    """
    Initialize the EGS cog.
    """
    bot.add_cog(EGS(bot))
