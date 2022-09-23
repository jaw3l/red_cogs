import io
import httpx
import discord
from datetime import datetime
from redbot.core import Config
from redbot.core import commands
from colorthief import ColorThief
from urllib.request import urlopen
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS


class EGS(commands.Cog):
    """
    **Fetches current and upcoming free games on Epic Games Store.**

    ```Syntax: [p]egs [upcoming/singly]```

    **Examples:** 
        - `[p]egs` - List current free games as menu
        - `[p]egs upcoming` - List upcoming free games as menu
        - `[p]egs list` - Send each free game as seperate message
    """

    def __init__(self, bot):
        self.bot = bot
        self.current_freegames = list()
        self.upcoming_freegames = list()

        default_member = {
            "locale": "en-US",
            "country": "TR",
            "allowCountries": "TR",
        }

        default_guild = {
            "database": []
        }

        self.config = Config.get_conf(self, identifier="EGS")
        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)

        self.url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=TR&allowCountries=TR"

    async def get_url(self, author):
        if await self.config.member(author).locale():
            locale = await self.config.member(author).locale()
            return f"https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country={locale}&allowCountries={locale}"
        else:
            return self.url

    async def getFreeGames(self, author):
        """
        Adds current free games and upcoming free games to a list
        _Şu anda ve ileride bedava olacak oyunları listeye ekler

        author: discord.Member
        returns: none
        """
        self.current_freegames.clear()
        URL = await self.get_url(author=author)
        response = httpx.get(URL)
        data = response.json()["data"]["Catalog"]["searchStore"]["elements"]

        for title in data:
            # Check if game has promotions
            if title["promotions"]:
                # Promotions --> UpcomingPromotionalOffers
                for upcoming in title["promotions"]["upcomingPromotionalOffers"]:
                    for discount in upcoming["promotionalOffers"]:
                        if discount["discountSetting"]["discountPercentage"] == 0:
                            self.upcoming_freegames.append(title['title'])

                # Promotions --> Promotional Offers
                for promotion in title["promotions"]["promotionalOffers"]:
                    for discount in promotion["promotionalOffers"]:
                        if discount["discountSetting"]["discountPercentage"] == 0:
                            self.current_freegames.append(title['title'])

    async def getGameInfo(self, author, game_title, current_freegame=True):
        """
        Returns game info as dictionary
        _Oyun bilgilerini sözlük olarak döndürür
        author: discord.Member
        game_title: str
        current_freegames: boolean
        returns: game_info (dict)
        """

        URL = await self.get_url(author=author)
        data = httpx.get(URL).json()["data"]["Catalog"]["searchStore"]["elements"]

        game_info = {
            "title": None,
            "publisher": None,
            "developer": None,
            "description": None,
            "offerType": None,
            "keyImages": None,
            "price": None,
            "promotionStartDate": None,
            "promotionEndData": None
        }

        for game in data:
            if game["title"] == game_title:
                game_info["title"] = game["title"]
                game_info["description"] = game["description"]

                if game["offerType"] == "BASE_GAME":
                    game_info["offerType"] = "Game"
                elif game["offerType"] == "ADD_ON":
                    game_info["offerType"] = "DLC"
                elif game["offerType"] == "DLC":
                    game_info["offerType"] = "DLC"

                for image in game["keyImages"]:
                    if image["type"] == "DieselStoreFrontWide":
                        game_info["keyImages"] = image["url"]
                    else:
                        if image["type"] == "OfferImageWide":
                            game_info["keyImages"] = image["url"]

                if game["seller"]["name"]:
                    game_info["publisher"] = game["seller"]["name"]
                else:
                    for attribute in game["customAttributes"]:
                        if attribute["key"] == "publisherName":
                            game_info["publisher"] = attribute["value"]

                for attribute in game["customAttributes"]:
                    if attribute["key"] == "developerName":
                        game_info["developer"] = attribute["value"]

                get_price = game["price"]["totalPrice"]["fmtPrice"]["originalPrice"]
                game_info["price"] = get_price

                for mapping in game["catalogNs"]["mappings"]:
                    game_info["url"] = f"https://www.epicgames.com/store/en-US/p/{mapping['pageSlug']}"

                if current_freegame:
                    for promotion in game["promotions"]["promotionalOffers"]:
                        for date in promotion["promotionalOffers"]:
                            game_info["promotionStartDate"] = date["startDate"]
                            game_info["promotionEndData"] = date["endDate"]
                else:
                    for promotion in game["promotions"]["upcomingPromotionalOffers"]:
                        for date in promotion["promotionalOffers"]:
                            game_info["promotionStartDate"] = date["startDate"]
                            game_info["promotionEndData"] = date["endDate"]

        return game_info

    async def getDominantColor(self, url, quality=10):
        """
        Finds dominant color in the image
        _Fotoğraftaki dominant rengi bulur
        url: str
        quality: int (default:10, yükseldikçe kalite düşer)
        returns: color (int)
        """

        color_read = ColorThief(io.BytesIO(urlopen(url).read()))
        color_hex = "%02x%02x%02x" % color_read.get_color(quality=quality)
        color = int("0x" + color_hex, 16)

        return color

    def findTimeDifference(self, date: str):
        """
        Finds difference between local isotime and given isotime
        _Yerel isotime ile verilen isotime arasındaki zaman farkını bulur
        date: str
        returns: timedelta (str)
        """

        date_now = datetime.now().isoformat(timespec="milliseconds")
        timedelta = datetime.strptime(
            date[:-1], "%Y-%m-%dT%H:%M:%S.%f") - datetime.strptime(date_now, "%Y-%m-%dT%H:%M:%S.%f")
        return str(timedelta)[:-7]

    def to_upper(arg):
        return arg.upper()

    @commands.group(name="egs", autohelp=False, invoke_without_command=True)
    async def _egs(self, ctx):
        """
        List current free games as menu.
        """

        author = ctx.author

        async with ctx.typing():
            get_free_games = await self.getFreeGames(author=author)
            free_games = self.current_freegames
            if not free_games:
                return await ctx.send("No free games found.")

            games = list()
            e = discord.Embed()
            for game in free_games:
                gameInfo = await self.getGameInfo(author=author, game_title=game)
                color = await self.getDominantColor(gameInfo["keyImages"])
                promo_date = datetime.fromisoformat(gameInfo["promotionStartDate"][:-5])
                format_date = promo_date.strftime("%d/%m/%Y")
                time_left = self.findTimeDifference(gameInfo["promotionEndData"])

                e.description = gameInfo["description"]
                e.set_footer(text=f"Valid until {format_date}.  {time_left} left.")
                e.set_author(name=gameInfo["title"], url=gameInfo["url"])
                e.set_image(url=gameInfo["keyImages"])
                e.add_field(name="Developer", value=gameInfo["developer"], inline=True)
                e.add_field(name="Publisher", value=gameInfo["publisher"], inline=True)
                e.add_field(name="Offer Type", value=gameInfo["offerType"], inline=True)
                e.add_field(name="Original Price", value=gameInfo["price"], inline=True)
                games.append(e)
                e = discord.Embed(color=color)

        await menu(ctx, games, DEFAULT_CONTROLS)

    @_egs.command(name="upcoming", aliases=["up", "egsu"])
    async def _upcoming(self, ctx):
        """
        List upcoming free games as menu.
        """

        author = ctx.author

        async with ctx.typing():
            get_free_games = await self.getFreeGames(author=author)
            free_games = self.upcoming_freegames
            if not free_games:
                return await ctx.send("No upcoming free games found.")

            games = list()
            e = discord.Embed()
            for game in free_games:
                gameInfo = await self.getGameInfo(author=author, game_title=game, current_freegame=False)
                color = await self.getDominantColor(gameInfo["keyImages"])
                promo_date = datetime.fromisoformat(gameInfo["promotionStartDate"][:-5])
                format_date = promo_date.strftime("%d/%m/%Y")
                time_left = self.findTimeDifference(gameInfo["promotionEndData"])

                e.description = gameInfo["description"]
                e.set_footer(text=f"Valid until {format_date}.  {time_left} left.")
                e.set_author(name=gameInfo["title"], url=gameInfo["url"])
                e.set_image(url=gameInfo["keyImages"])
                e.add_field(name="Developer", value=gameInfo["developer"], inline=True)
                e.add_field(name="Publisher", value=gameInfo["publisher"], inline=True)
                e.add_field(name="Offer Type", value=gameInfo["offerType"], inline=True)
                e.add_field(name="Original Price", value=gameInfo["price"], inline=True)
                games.append(e)
                e = discord.Embed(color=color)

        await menu(ctx, games, DEFAULT_CONTROLS)

    @_egs.command(name="singly", aliases=["list", "single", "1by1"])
    async def _singly(self, ctx):
        """
        Print current free games one by one.
        """

        author = ctx.author

        async with ctx.typing():
            get_free_games = await self.getFreeGames(author=author)
            free_games = self.current_freegames
            if not free_games:
                return await ctx.send("No free games found.")

            games = list()
            for game in free_games:
                gameInfo = await self.getGameInfo(author=author, game_title=game)
                color = await self.getDominantColor(gameInfo["keyImages"])
                promo_date = datetime.fromisoformat(gameInfo["promotionStartDate"][:-5])
                format_date = promo_date.strftime("%d/%m/%Y")
                time_left = self.findTimeDifference(gameInfo["promotionEndData"])

                e = discord.Embed(color=color)
                e.description = gameInfo["description"]
                e.set_footer(text=f"Valid until {format_date}.  {time_left} left.")
                e.set_author(name=gameInfo["title"], url=gameInfo["url"])
                e.set_image(url=gameInfo["keyImages"])
                e.add_field(name="Developer", value=gameInfo["developer"], inline=True)
                e.add_field(name="Publisher", value=gameInfo["publisher"], inline=True)
                e.add_field(name="Offer Type", value=gameInfo["offerType"], inline=True)
                e.add_field(name="Original Price", value=gameInfo["price"], inline=True)
                games.append(e)

                await ctx.send(embed=e)

    @_egs.group(name="settings", aliases=["s"], autohelp=True)
    async def _settings(self, ctx):
        """
        EGS Settings
        \n
        **Examples:**
            - `[p]egs settings locale`
            *or you can use aliases*
            - `[p]egs s l`
        """
        pass

    @_settings.group(name="locale", aliases=["l"], autohelp=True)
    async def _locale(self, ctx):
        """
        EGS Locale Settings
        \n
        **Examples:**
            - `[p]egs settings locale get` - Gets current locale setting
            - `[p]egs settings locale set <COUNTRY_CODE>` - Sets current locale setting
            - `[p]egs settings locale del` - Deletes current locale setting
        """
        pass

    @_locale.command(name="get", aliases=["g"])
    async def _get_locale(self, ctx):
        """
        Get current locale setting
        """
        guild = ctx.guild
        author = ctx.author
        database = await self.config.guild(guild).database()
        userdata = await self.config.member(author).all()
        if author.id not in database:
            database.append(author.id)
            await self.config.guild(guild).database.set(database)
        data = discord.Embed(colour=author.colour)
        data.add_field(name="EGS Locale Setting",
                       value=f"Locale is **{await self.config.member(author).locale()}**")
        await ctx.send(embed=data)

    @_locale.command(name="set", aliases=["s"])
    async def _set_locale(self, ctx, new_value: to_upper):
        """
        Set current locale setting
        """
        guild = ctx.guild
        author = ctx.author
        database = await self.config.guild(guild).database()
        userdata = await self.config.member(author).all()
        if author.id not in database:
            database.append(author.id)
            await self.config.guild(guild).database.set(database)
        await self.config.member(author).locale.set(new_value)
        data = discord.Embed(colour=author.colour)
        data.add_field(name="EGS Locale Setting",
                       value=f"New locale is set to **{await self.config.member(author).locale()}**")
        await ctx.send(embed=data)

    @_locale.command(name="del", aliases=["d"])
    async def _del_locale(self, ctx):
        """
        Delete current locale setting
        """
        author = ctx.author
        await self.config.member(author).locale.clear()
        data = discord.Embed(colour=author.colour)
        data.add_field(name="EGS Locale Setting",
                       value="Deleted locale setting.")
        await ctx.send(embed=data)
