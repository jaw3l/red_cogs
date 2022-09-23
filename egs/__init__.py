from .main import EGS


def setup(bot):
    """
    Initialize the EGS cog.
    """
    bot.add_cog(EGS(bot))
