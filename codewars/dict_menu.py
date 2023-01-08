# Original source of reaction-based menu idea from
# https://github.com/Lunar-Dust/Dusty-Cogs/blob/master/menu/menu.py
#
# Ported to Red V3 by Palm\_\_ (https://github.com/palmtree5)

# This is a edited version of the original code from Red V3 (https://docs.discord.red/en/stable/_modules/redbot/core/utils/menus.html)

import asyncio
import contextlib
import functools
from typing import Iterable, List, Union

import discord
from redbot.core import commands
from redbot.core.utils.predicates import ReactionPredicate

_ReactableEmoji = Union[str, discord.Emoji]


async def dict_menu(
    ctx: commands.Context,
    page_content: Union[List[str], List[discord.Embed]],
    controls: dict,
    embed_per_page: int = 5,
    page_number: int = 0,
    timeout: float = 30.0,
    message: discord.Message = None,
):
    """
    An emoji-based menu for Red V3.

    Parameters
    ----------
    ctx: commands.Context
        The command context
    page_content: `list`
        The content of the page of the menu.
    controls: dict
        A mapping of emoji to the function which handles the action for the
        emoji.
    embed_per_page: int
        The number of embeds per page. Defaults to 5.
    page_number: int
        The current page number of the menu
    timeout: float
        The time (in seconds) to wait for a reaction

    Raises
    ------
    RuntimeError
        If either of the notes above are violated
    """

    for key, value in controls.items():
        maybe_coro = value
        if isinstance(value, functools.partial):
            maybe_coro = value.func
        if not asyncio.iscoroutinefunction(maybe_coro):
            raise RuntimeError("Function must be a coroutine")

    dict_page_content: dict = {}
    total_page_number: int = 0

    if len(page_content) <= embed_per_page:
        dict_page_content.update({total_page_number: page_content})
    else:
        # Divide the page content into pages using the embed_per_page parameter
        for item in range(0, len(page_content), embed_per_page):
            dict_page_content.update({total_page_number: page_content[item:item + embed_per_page]})
            total_page_number += 1

    if page_number < total_page_number:
        current_page = dict_page_content[page_number][0]
    else:
        current_page = dict_page_content[0][-1]

    if not message:
        if isinstance(current_page, discord.Embed):
            message = await ctx.send(embed=current_page)
        else:
            message = await ctx.send(current_page)
        # Don't wait for reactions to be added (GH-1797)
        # noinspection PyAsyncCall
        start_adding_reactions(message, controls.keys())
    else:
        try:
            if isinstance(current_page, discord.Embed):
                await message.edit(embed=current_page)
            else:
                await message.edit(content=current_page)
        except discord.NotFound:
            return

    start_adding_reactions(message, controls.keys())

    try:
        react, user = await ctx.bot.wait_for(
            "reaction_add",
            check=ReactionPredicate.with_emojis(tuple(controls.keys()), message, ctx.author),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        if not ctx.me:
            return
        try:
            if message.channel.permissions_for(ctx.me).manage_messages:
                await message.clear_reactions()
            else:
                raise RuntimeError
        except (discord.Forbidden, RuntimeError):  # cannot remove all reactions
            for key in controls.keys():
                try:
                    await message.remove_reaction(key, ctx.bot.user)
                except discord.Forbidden:
                    return
                except discord.HTTPException:
                    pass
        except discord.NotFound:
            return
    else:
        return await controls[react.emoji](
            ctx,
            page_content,
            controls,
            embed_per_page,
            page_number,
            timeout,
            message,
            react.emoji,
            total_page_number,
        )


async def next_page(
    ctx: commands.Context,
    page_content: list,
    controls: dict,
    embed_per_page: int,
    page_number: int,
    timeout: float,
    message: discord.Message,
    emoji: str,
    total_page_number: int,
):
    embed_per_page = embed_per_page
    perms = message.channel.permissions_for(ctx.me)
    if perms.manage_messages:  # Can manage messages, so remove react
        with contextlib.suppress(discord.NotFound):
            await message.remove_reaction(emoji, ctx.author)
    if page_number == total_page_number - 1:
        page_number = 0  # Loop around to the first item
    else:
        page_number += 1
    return await dict_menu(ctx,
                           page_content=page_content,
                           controls=controls,
                           embed_per_page=embed_per_page,
                           page_number=page_number,
                           timeout=timeout,
                           message=message,
                           )


async def prev_page(
    ctx: commands.Context,
    page_content: list,
    controls: dict,
    embed_per_page: int,
    page_number: int,
    timeout: float,
    message: discord.Message,
    emoji: str,
    total_page_number: int,
):
    embed_per_page = embed_per_page
    perms = message.channel.permissions_for(ctx.me)
    if perms.manage_messages:  # Can manage messages, so remove react
        with contextlib.suppress(discord.NotFound):
            await message.remove_reaction(emoji, ctx.author)
    if page_number == 0:
        page_number = total_page_number - 1  # Loop around to the last item
    else:
        page_number -= 1
    return await dict_menu(ctx,
                           page_content=page_content,
                           controls=controls,
                           embed_per_page=embed_per_page,
                           page_number=page_number,
                           timeout=timeout,
                           message=message,
                           )


async def close_menu(
    ctx: commands.Context,
    page_content: list,
    controls: dict,
    embed_per_page: int,
    page_number: int,
    timeout: float,
    message: discord.Message,
    emoji: str,
    total_page_number: int,
):
    with contextlib.suppress(discord.NotFound):
        await message.delete()


def start_adding_reactions(
    message: discord.Message,
    emojis: Iterable[_ReactableEmoji]
) -> asyncio.Task:
    """Start adding reactions to a message.

    This is a non-blocking operation - calling this will schedule the
    reactions being added, but the calling code will continue to
    execute asynchronously. There is no need to await this function.

    This is particularly useful if you wish to start waiting for a
    reaction whilst the reactions are still being added - in fact,
    this is exactly what `menu` uses to do that.

    Parameters
    ----------
    message: discord.Message
        The message to add reactions to.
    emojis : Iterable[Union[str, discord.Emoji]]
        The emojis to react to the message with.

    Returns
    -------
    asyncio.Task
        The task for the coroutine adding the reactions.

    """

    async def task():
        # The task should exit silently if the message is deleted
        with contextlib.suppress(discord.NotFound):
            for emoji in emojis:
                await message.add_reaction(emoji)

    return asyncio.create_task(task())


DICT_CONTROLS = {
    "\N{LEFTWARDS BLACK ARROW}\N{VARIATION SELECTOR-16}": prev_page,
    "\N{CROSS MARK}": close_menu,
    "\N{BLACK RIGHTWARDS ARROW}\N{VARIATION SELECTOR-16}": next_page,
}
