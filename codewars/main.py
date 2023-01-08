import time
import httpx
import discord
import datetime
from lxml import html
from redbot.core import Config, commands
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from redbot.core.utils.predicates import ReactionPredicate
from .errors import CodewarsBadRequest, CodewarsUnauthorized, CodewarsForbidden, CodewarsNotFound
from .dict_menu import dict_menu, DICT_CONTROLS


class Codewars(commands.Cog):
    """
    **Codewars**

    ```Syntax: [p]codewars```

    **Examples:**
        - `[p]codewars` - Get your codewars profile
        *or you can use aliases*
        - `[p]cw`
    """

    def __init__(self, bot):
        self.bot = bot

        # Config
        default_user = {"username": ""}
        self.config = Config.get_conf(self, identifier="0xC0D3W4R8")
        self.config.register_user(**default_user)

    async def format_color(self, color: str) -> int:
        """Formats a color string to a hex value

        Args:
            color (str): Color string

        Returns:
            int: Hex value of color
        """
        colors = {"white": 0xFFFFFF, "yellow": 0xFFFF00, "blue": 0x0000FF,
                  "purple": 0x800080, "black": 0x000000, "red": 0xFF0000}
        return colors.get(color, 0xFFFFFF)

    async def get_user_avatar(self, user):
        url = f"https://www.codewars.com/users/{user}"
        xpath = "//div[1]/div[1]/main/div[3]/section/div/figure/a/img/@src"
        request = httpx.get(url).content
        tree = html.fromstring(request)
        return tree.xpath(xpath)[0]

    async def get_kata(self, id: str) -> dict:
        url = f"https://www.codewars.com/api/v1/code-challenges/{id}"
        try:
            request = httpx.get(url)
            response = request.json()
            kata_info = {
                "id": response["id"],
                "name": response["name"],
                "slug": response["slug"],
                "url": response["url"],
                "category": response["category"],
                "description": response["description"],
                "tags": response["tags"],
                "languages": response["languages"],
                "rank_name": response["rank"]["name"],
                "rank_color": response["rank"]["color"],
                "created_by_username": response["createdBy"]["username"],
                "created_by_url": response["createdBy"]["url"],
                "total_attempts": response["totalAttempts"],
                "total_completed": response["totalCompleted"],
                "total_stars": response["totalStars"],
                "vote_score": response["voteScore"],
                "published_at": response["publishedAt"],
                "approved_at": response["approvedAt"],
            }

            kata_info["rank_color"] = await self.format_color(kata_info["rank_color"])

            if kata_info["approved_at"] is None:
                kata_info["approved_at"] = "Unknown"
            else:
                kata_info["approved_by_url"] = response["approvedBy"]["url"]
                kata_info["approved_by_username"] = response["approvedBy"]["username"]

            result = {
                "kata_info": kata_info,
                "message": "success"
            }
            return result
        except KeyError:
            result = {
                "message": "Error, kata not found. Please make sure you have the correct kata ID or slug."
            }
            return result

    async def get_user(self, user):
        url = f"https://www.codewars.com/api/v1/users/{user}"
        request = httpx.get(url)
        if request.status_code == 200:
            response = request.json()
            user_info = {
                "username": response["username"],
                "name": response["name"],
                "honor": response["honor"],
                "leaderboardPosition": response["leaderboardPosition"],
                "clan": response["clan"],
                "overall_rank": response["ranks"]["overall"]["name"],
                "overall_colour": response["ranks"]["overall"]["color"],
                "overall_score": response["ranks"]["overall"]["score"],
                "totalCompleted": response["codeChallenges"]["totalCompleted"],
                "skills": response["skills"],
                "languages": response["ranks"]["languages"],
            }

            user_info["overall_colour"] = await self.format_color(user_info["overall_colour"])

            return user_info
        else:
            raise Exception("Error, user not found.")

    async def get_latest_completed(self, user: str, page: int = 0, limit: int = 10) -> list:
        url = f"https://www.codewars.com/api/v1/users/{user}/code-challenges/completed?page={page}"
        request = httpx.get(url)
        if limit <= 20:
            if request.status_code == 200:
                response = request.json()
                if response["totalItems"] < 1:
                    raise CodewarsNotFound("No completed katas found.")
                else:
                    return response["data"][:limit]
            else:
                raise Exception("Error, user not found.")
        else:
            raise Exception("Limit must be less than 20.")

    async def iso_to_unix(self, iso: str) -> int:
        """Converts ISO 8601 time to unix (epoch) time

        Args:
            iso (str): ISO 8601 time

        Returns:
            int: Unix time
        """
        if iso == "Unknown":
            return 0
        else:
            return int(time.mktime(datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%S.%fZ").timetuple()))

    async def format_description(self, description: str) -> str:
        """Formats the description of a kata to be more readable in Discord. 
        Replaces <br> with new lines and headings with bold characters.

        Args:
            description (str): Description of kata

        Returns:
            str: Formatted description
        """
        # Check if description has "description" heading
        if not description.startswith("## Description"):
            description = "** Description **\n" + description
        # Format headings to bold characters
        while True:
            if description.find("## ") == -1:
                break
            find_heading = description.find("## ")
            find_heading_end = description.find("\n", find_heading)
            description = description.replace(
                description[find_heading: find_heading_end],
                f"**{description[find_heading+3:find_heading_end]}**")
        description = description.replace("<br>", "\n")
        return description

    @commands.group(name="codewars", autohelp=False, invoke_without_command=True, aliases=["cw"])
    async def _codewars(self, ctx, user=None):
        """
        Get information about your codewars profile
        """
        if not user:
            username = await self.config.user(ctx.author).username()
            if not username:
                return await ctx.send(f"You haven't registered your username yet. Use `{ctx.prefix}codewars settings username set <username>` to register.")
            else:
                async with ctx.typing():
                    try:
                        userInfo = await self.get_user(user=username)
                        data = discord.Embed(colour=userInfo["overall_colour"])
                        data.set_author(
                            name=f"Codewars Stats of {userInfo['username']}",
                            url=f"https://www.codewars.com/users/{userInfo['username']}",
                            icon_url="https://avatars.githubusercontent.com/u/5387632?s=200")
                        if userInfo["name"]:
                            data.description = userInfo["name"]
                        data.set_thumbnail(url=await self.get_user_avatar(user=username))
                        data.add_field(name="Overall Rank", value=userInfo["overall_rank"], inline=True)
                        data.add_field(name="Overall Score", value=userInfo["overall_score"], inline=True)
                        data.add_field(name="Total Completed", value=userInfo["totalCompleted"], inline=True)
                        data.add_field(name="Leaderboard Position", value=userInfo["leaderboardPosition"], inline=True)
                        data.add_field(name="Honor", value=userInfo["honor"], inline=True)
                        data.add_field(name="Clan", value=userInfo["clan"], inline=True)
                        data.set_footer(text="© Codewars")
                        data.timestamp = datetime.datetime.utcnow()
                        return await ctx.send(embed=data)
                    except Exception as Error:
                        data = discord.Embed(colour=discord.Colour.red())
                        data.add_field(name="Codewars Error", value=Error)
                        return await ctx.send(embed=data)
        else:
            async with ctx.typing():
                try:
                    userInfo = await self.get_user(user=ctx.message.content.split(" ")[1])
                    data = discord.Embed(colour=userInfo["overall_colour"])
                    data.set_author(
                        name=f"Codewars Stats of {userInfo['username']}",
                        url=f"https://www.codewars.com/users/{userInfo['username']}",
                        icon_url="https://avatars.githubusercontent.com/u/5387632?s=200")
                    if userInfo["name"]:
                        data.description = userInfo["name"]
                    data.set_thumbnail(url=await self.get_user_avatar(user=ctx.message.content.split(" ")[1]))
                    data.add_field(name="Overall Rank", value=userInfo["overall_rank"], inline=True)
                    data.add_field(name="Overall Score", value=userInfo["overall_score"], inline=True)
                    data.add_field(name="Total Completed", value=userInfo["totalCompleted"], inline=True)
                    data.add_field(name="Leaderboard Position", value=userInfo["leaderboardPosition"], inline=True)
                    data.add_field(name="Honor", value=userInfo["honor"], inline=True)
                    data.add_field(name="Clan", value=userInfo["clan"], inline=True)
                    data.set_footer(text="© Codewars")
                    data.timestamp = datetime.datetime.utcnow()
                    return await ctx.send(embed=data)
                except Exception as Error:
                    data = discord.Embed(colour=discord.Colour.red())
                    data.add_field(name="Codewars Error", value=Error)
                    return await ctx.send(embed=data)

    @_codewars.command(name="languages", aliases=["l", "lang"], autohelp=True)
    async def _languages(self, ctx, user=None):
        """
        List per language stats as menu
        \n
        **Examples:**
            - `[p]codewars languages <username>`
            - `[p]codewars languages` # If you have registered your username
            *or you can use aliases*
            - `[p]cw l <username>`
            - `[p]cw l` # If you have registered your username
        """

        language_images = {"c": "https://i.imgur.com/IgMT4VW.png",
                           "clojure": "https://i.imgur.com/SsEWBmW.png",
                           "coffeescript": "https://i.imgur.com/rEWxYhv.png",
                           "cpp": "https://i.imgur.com/O5BcX33.png",
                           "csharp": "https://i.imgur.com/IdlAR1B.png",
                           "go": "https://i.imgur.com/JCA1E0Q.png",
                           "groovy": "https://i.imgur.com/BoWWCFx.png",
                           "haskell": "https://i.imgur.com/MRXo1U0.png",
                           "java": "https://i.imgur.com/HbzHc9Z.png",
                           "javascript": "https://i.imgur.com/8DFw5s9.png",
                           "kotlin": "https://i.imgur.com/Kbdj3tB.png",
                           "lua": "https://i.imgur.com/1gvQNMh.png",
                           "ocaml": "https://i.imgur.com/coYXRb6.png",
                           "php": "https://i.imgur.com/PHxL185.png",
                           "powershell": "https://i.imgur.com/fHIAYGk.png",
                           "python": "https://i.imgur.com/DCBz8dd.png",
                           "r": "https://i.imgur.com/FQS2tdC.png",
                           "ruby": "https://i.imgur.com/W0bXkco.png",
                           "rust": "https://i.imgur.com/BExi1sJ.png",
                           "scala": "https://i.imgur.com/S9tRrcr.png",
                           "swift": "https://i.imgur.com/3xCT5PY.png",
                           "typescript": "https://i.imgur.com/dUsR3e4.png",
                           }
        async with ctx.typing():
            if user:
                userInfo = await self.get_user(user=user)
                userAvatar = await self.get_user_avatar(user=user)
                languages = []
                try:
                    if userInfo["languages"]:
                        data = discord.Embed()
                        for language, stats in userInfo["languages"].items():
                            data.set_author(
                                name=f"Codewars Stats of {userInfo['username']}",
                                url=f"https://www.codewars.com/users/{userInfo['username']}",
                                icon_url=userAvatar)
                            if language in language_images:
                                # TODO_2: Add language images as Discord attachments
                                # Example: https://stackoverflow.com/a/67679689/11017223
                                # language_image = discord.File(f"{str(bundled_data_path(self))}/{language}.png")
                                # data.set_thumbnail(url=f"attachment://{language}.png")
                                data.set_thumbnail(url=language_images.get(language))
                            data.add_field(name="Language", value=language.capitalize(), inline=True)
                            data.add_field(name="Rank", value=stats.get("name"), inline=True)
                            data.add_field(name="Score", value=stats.get("score"), inline=True)
                            data.set_footer(text="© Codewars",
                                            icon_url="https://avatars.githubusercontent.com/u/5387632?s=50")
                            data.timestamp = datetime.datetime.utcnow()
                            data.colour = await self.format_color(stats.get("color"))
                            languages.append(data)
                            data = discord.Embed()
                        #TODO_2: await menu(ctx, languages, DEFAULT_CONTROLS, file=language_image)
                        await menu(ctx, languages, DEFAULT_CONTROLS)
                except Exception as Error:
                    data = discord.Embed(colour=discord.Colour.red())
                    data.add_field(name="Codewars Error", value=Error)
                    return await ctx.send(embed=data)
            else:
                username = await self.config.user(ctx.author).username()
                if not username:
                    embed = discord.Embed(colour=discord.Colour.red())
                    embed.add_field(
                        name="Codewars Error",
                        value="You have not set your username yet. Use `codewars set <username>` to set your username.")
                    return await ctx.send(embed=embed)
                else:
                    userInfo = await self.get_user(user=username)
                    userAvatar = await self.get_user_avatar(user=username)
                    languages = []
                try:
                    if userInfo["languages"]:
                        data = discord.Embed()
                        for language, stats in userInfo["languages"].items():
                            data.set_author(
                                name=f"Codewars Stats of {userInfo['username']}",
                                url=f"https://www.codewars.com/users/{userInfo['username']}",
                                icon_url=userAvatar)
                            if language in language_images:
                                data.set_thumbnail(url=language_images.get(language))
                            data.add_field(name="Language", value=language.capitalize(), inline=True)
                            data.add_field(name="Rank", value=stats.get("name"), inline=True)
                            data.add_field(name="Score", value=stats.get("score"), inline=True)
                            data.set_footer(text="© Codewars",
                                            icon_url="https://avatars.githubusercontent.com/u/5387632?s=50")
                            data.timestamp = datetime.datetime.utcnow()
                            data.colour = await self.format_color(stats.get("color"))
                            languages.append(data)
                            data = discord.Embed()
                        await menu(ctx, languages, DEFAULT_CONTROLS)
                except Exception as Error:
                    data = discord.Embed(colour=discord.Colour.red())
                    data.add_field(name="Codewars Error", value=Error)
                    return await ctx.send(embed=data)

    @_codewars.command(name="skills", aliases=["sk", "skill"], autohelp=False)
    async def _skills(self, ctx, user=None):
        """
        List users skills
        \n
        **Examples:**
            - `[p]codewars skills <username>`
            - `[p]codewars skills` # If you have set your username
            *or you can use aliases*
            - `[p]cw sk <username>`
            - `[p]cw sk` # If you have set your username
        """
        async with ctx.typing():
            if not user:
                username = await self.config.user(ctx.author).username()
                if not username:
                    return await ctx.send(f"You haven't registered your username yet. Use `{ctx.prefix}codewars settings username set <username>` to register.")
                else:
                    userInfo = await self.get_user(user=username)
                    data = discord.Embed(colour=userInfo["overall_colour"])
                    data.set_author(
                        name=f"Codewars Skills of {userInfo['username']}",
                        url=f"https://www.codewars.com/users/{userInfo['username']}",
                        icon_url="https://avatars.githubusercontent.com/u/5387632?s=200")
                    data.set_thumbnail(url=await self.get_user_avatar(user=username))
                    data.add_field(name="Skills", value=userInfo["skills"])
                    data.timestamp = datetime.datetime.utcnow()
                    data.set_footer(text="© Codewars")
                    await ctx.send(embed=data)
            else:
                userInfo = await self.get_user(user=user)
                data = discord.Embed(colour=userInfo["overall_colour"])
                data.set_author(
                    name=f"Codewars Skills of {userInfo['username']}",
                    url=f"https://www.codewars.com/users/{userInfo['username']}",
                    icon_url="https://avatars.githubusercontent.com/u/5387632?s=200")
                data.set_thumbnail(url=await self.get_user_avatar(user=ctx.message.content.split(" ")[1]))
                data.add_field(name="Skills", value=userInfo["skills"])
                data.timestamp = datetime.datetime.utcnow()
                data.set_footer(text="© Codewars")
                await ctx.send(embed=data)

    @_codewars.command(name="completed", autohelp=False)
    async def _completed(self, ctx, user=None, limit: int = 10):
        """
        List last 5 to 20 completed katas as menu
        """
        async with ctx.typing():
            # If user is not provided, get username from config
            if not user:
                try:
                    username = await self.config.user(ctx.author).username()
                    if not username:
                        return await ctx.send(f"You haven't registered your username yet. Use `{ctx.prefix}codewars settings username set <username>` to register.")
                    else:
                        userInfo = await self.get_user(user=username)
                        userAvatar = await self.get_user_avatar(user=username)
                        completedKatas = await self.get_latest_completed(user=username, limit=limit)

                        kataList = []
                        kata_count = 0

                        embed = discord.Embed()
                        for kata in completedKatas:
                            if kata_count == 5:
                                embed = discord.Embed()
                                kata_count = 0

                            kataInfo = await self.get_kata(id=kata["id"])
                            kataInfo = kataInfo.get("kata_info", {})

                            embed.set_author(
                                name=f"Last {limit} Completed Katas of {userInfo['username']}",
                                url=f"https://www.codewars.com/users/{userInfo['username']}/completed",
                                icon_url="https://avatars.githubusercontent.com/u/5387632?s=50")
                            embed.set_thumbnail(url=userAvatar)
                            embed.add_field(
                                name=kataInfo.get("name", "Unknown").title(),
                                value=f"""**Rank:** {kataInfo.get("rank_name", "N/A")}
                                **Category:** {kataInfo.get("category", "N/A").capitalize()}
                                **Completed/Attempts:** {kataInfo.get('total_completed', 'N/A')} / {kataInfo.get('total_attempts', 'N/A')}
                                **Completed At:** <t:{await self.iso_to_unix(iso=kata.get('completedAt', 'N/A'))}:R>
                                **Completed Languages:** {', '.join(kata.get('completedLanguages', 'N/A'))}
                                [[Go To Kata]({kataInfo.get('url', 'https://www.codewars.com')})]""",
                                inline=False)
                            embed.timestamp = datetime.datetime.utcnow()
                            embed.color = kataInfo.get("rank_color", 0x000000)

                            kataList.append(embed)
                            kata_count += 1

                        await dict_menu(ctx, kataList, DICT_CONTROLS)

                except Exception as Error:
                    embed = discord.Embed(colour=discord.Colour.red())
                    embed.add_field(name="Codewars Error", value=Error)
                    return await ctx.send(embed=embed)
            else:
                try:
                    userInfo = await self.get_user(user=user)
                    userAvatar = await self.get_user_avatar(user=user)
                    completedKatas = await self.get_latest_completed(user=user, limit=limit)

                    kataList = []
                    kata_count = 0

                    embed = discord.Embed()
                    for kata in completedKatas:
                        if kata_count == 5:
                            embed = discord.Embed()
                            kata_count = 0

                        kataInfo = await self.get_kata(id=kata["id"])
                        kataInfo = kataInfo.get("kata_info", {})

                        embed.set_author(
                            name=f"Last {limit} Completed Katas of {userInfo['username']}",
                            url=f"https://www.codewars.com/users/{userInfo['username']}/completed",
                            icon_url="https://avatars.githubusercontent.com/u/5387632?s=10")
                        embed.set_thumbnail(url=userAvatar)
                        embed.add_field(
                            name=kataInfo.get("name", "Unknown").title(),
                            value=f"""**Rank:** {kataInfo.get("rank_name", "N/A")}
                            **Category:** {kataInfo.get("category", "N/A").capitalize()}
                            **Completed/Attempts:** {kataInfo.get('total_completed', 'N/A')} / {kataInfo.get('total_attempts', 'N/A')}
                            **Completed At:** <t:{await self.iso_to_unix(iso=kata.get('completedAt', 'N/A'))}:R>
                            **Completed Languages:** {', '.join(kata.get('completedLanguages', 'N/A'))}
                            [[Go To Kata]({kataInfo.get('url', 'https://www.codewars.com')})]""",
                            inline=False)
                        embed.timestamp = datetime.datetime.utcnow()
                        embed.color = kataInfo.get("rank_color", 0x000000)

                        kataList.append(embed)
                        kata_count += 1
                    await dict_menu(ctx, kataList, DICT_CONTROLS)

                # TODO: Get avarage rank of all katas and display rank colour accordingly

                except Exception as Error:
                    embed = discord.Embed(colour=discord.Colour.red())
                    embed.add_field(name="Codewars Error", value=Error)
                    return await ctx.send(embed=embed)

    @_codewars.command(name="kata", autohelp=False)
    async def _kata(self, ctx, id: str):
        """
        Get information about a kata.
        """
        async with ctx.typing():
            try:
                result = await self.get_kata(id=id)
                kataInfo = result.get("kata_info", {})
                embed = discord.Embed(colour=kataInfo.get("rank_color", 0xFFFFFF))
                embed.set_author(
                    name=kataInfo.get("name", "Unknown").title(),
                    url=f"https://www.codewars.com/kata/{kataInfo.get('id', 'Unknown')}",
                    icon_url="https://avatars.githubusercontent.com/u/5387632?s=200")
                embed.description = await self.format_description(description=kataInfo.get("description", "Unknown"))
                # Row 1
                embed.add_field(name="Rank", value=kataInfo.get("rank_name", "Unknown"))
                embed.add_field(name="Category", value=kataInfo.get("category", "Unknown").capitalize())
                embed.add_field(
                    name="Author",
                    value=f"[{kataInfo.get('created_by_username', 'Unknown')}]({kataInfo.get('created_by_url', 'Unknown')})")
                # Row 2
                embed.add_field(name="Attempts", value=kataInfo.get("total_attempts", "Unknown"))
                embed.add_field(name="Completed", value=kataInfo.get("total_completed", "Unknown"))
                embed.add_field(name="Stars", value=kataInfo.get("total_stars", "Unknown"))
                # Row 3
                embed.add_field(name="Score", value=kataInfo.get("vote_score", "Unknown"))
                embed.add_field(name="Published At", value=f"<t:{await self.iso_to_unix(iso=kataInfo.get('published_at', 'Unknown'))}:f>")
                if kataInfo["approved_at"] != "Unknown":
                    embed.add_field(name="Approved At", value=f"<t:{await self.iso_to_unix(iso=kataInfo.get('approved_at', 'Unknown'))}:f>")
                else:
                    embed.add_field(name="Approved", value="❌")
                # Footer
                embed.timestamp = datetime.datetime.utcnow()
                embed.set_footer(text="© Codewars")
                await ctx.send(embed=embed)
            except KeyError as ke:
                await ctx.send(ke)

    @_codewars.command(name="avatar", aliases=["a", "av"], autohelp=False)
    async def _avatar(self, ctx, user: str):
        """
        Get user's avatar from Codewars
        \n
        **Examples:**
            - `[p]codewars avatar <username>`
            *or you can use aliases*
            - `[p]cw a <username>`
        """
        await ctx.send(await self.get_user_avatar(user=user))

    @_codewars.command(name="test", autohelp=False)
    async def _test(self, ctx, language: str):
        """
        attach image to discord and display language image
        """
        
        language_image = discord.File(f"{str(bundled_data_path(self))}/{language}.png")
        
        embed = discord.Embed()
        embed.set_image(url=f"attachment://{language}.png")
        
        await ctx.send(embed=embed, file=language_image)

    @_codewars.group(name="settings", aliases=["s"], autohelp=True)
    async def _settings(self, ctx):
        """
        Codewars Settings
        \n
        **Examples:**
            - `[p]codewars settings username`
            *or you can use aliases*
            - `[p]cw s u`
        """
        pass

    @_settings.group(name="username", aliases=["u"], autohelp=True)
    async def _username(self, ctx):
        """
        Codewars Username Settings
        \n
        **Examples:**
            - `[p]codewars settings username get` - Gets current username
            - `[p]codewars settings username set <username>` - Sets current username
            - `[p]codewars settings username del` - Deletes current Codewars username
            *or you can use aliases*
            - `[p]cw s u g` - Gets current username
            - `[p]cw s u s <username>` - Sets current username
            - `[p]cw s u d` - Deletes current Codewars username
        """
        pass

    @_username.command(name="get", aliases=["g"])
    async def _get_username(self, ctx):
        """
        Get current Codewars username from database.
        \n
        **Examples:**
            - `[p]codewars settings username get`
            *or you can use aliases*
            - `[p]cw s u g`
        """
        username = await self.config.user(ctx.author).username()
        data = discord.Embed(colour=ctx.author.colour)

        if username:
            data.add_field(name="Codewars Username Settings", value=f"Current username: `{username}`")
            await ctx.send(embed=data)
        else:
            data.add_field(
                name="Codewars Username Settings",
                value=f"You haven't set your default Codewars username yet. Use `{ctx.prefix}codewars settings username set <username>` to set.")
            await ctx.send(embed=data)

    @_username.command(name="set", aliases=["s"])
    async def _set_username(self, ctx, new_value):
        """
        Set Codewars username.
        \n
        **Examples:**
            - `[p]codewars settings username set <username>`
            *or you can use aliases*
            - `[p]cw s u s <username>``        
        """
        await self.config.user(ctx.author).username.set(new_value)
        data = discord.Embed(colour=ctx.author.colour)
        data.add_field(name="Codewars Username Setting",
                       value=f"Your default Codewars username is set to **{new_value}**")
        await ctx.send(embed=data)

    @_username.command(name="delete", aliases=["d, del"])
    async def _delete_username(self, ctx):
        """
        Delete Codewars username from database.
        \n
        **Examples:**
            - `[p]codewars settings username delete`
            *or you can use aliases*
            - `[p]cw s u d`
        """
        await self.config.user(ctx.author).username.clear()
        data = discord.Embed(colour=ctx.author.colour)
        data.add_field(name="Codewars Username Setting",
                       value="Deleted default Codewars username from database.")
        await ctx.send(embed=data)
