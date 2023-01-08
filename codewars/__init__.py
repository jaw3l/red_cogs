from .main import Codewars


def setup(bot):
    bot.add_cog(Codewars(bot))
