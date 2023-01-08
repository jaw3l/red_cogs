# Red Bot Cogs

Cogs for the [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot) by [Cog Creators](https://github.com/Cog-Creators). Cogs in this repo can only be used with the V3 version.

## Installation

To add the repo to the repository manager:

`[p]repo add j3cogs https://github.com/jaw3l/red_cogs`

To install from the repo:

`[p]repo install j3cogs <cog_name>`

## Cogs

### EGS

Fetches free games from Epic Games Store.

#### Usage

`[p]egs` - Lists current week's free games as a menu

`[p]egs upcoming` - Lists upcoming week's free games as a menu

`[p]egs list` - Lists current week's games one by one

#### Requirements

You can install the requirements seperately:

`[p]pipinstall colorthief` - Required for getting dominant color of game's cover image

`[p]pipinstall datetime` - Required for parsing dates

`[p]pipinstall httpx` - Required for fetching data from Epic Games Store

Or you can use one command to install all requirements:

`[p]pipinstall colorthief datetime httpx`

### Codewars

Fethes data from Codewars. It can fetch:

- User's profile information
- Last completed katas
- User's skills
- User's languages
- Information about a specific kata

#### Usage

`[p]codewars <username>` - Fetches user's profile information

`[p]codewars completed <username>` - Fetches user's last completed katas

`[p]codewars skills <username>` - Fetches user's skills

`[p]codewars languages <username>` - Fetches user's languages

`[p]codewars kata <kata_id>` - Fetches information about a specific kata

**Tips:**

- You can use aliases for commands. For example, you can use `[p]cw` instead of `[p]codewars`.
- You can save your username to the database using `[p]settings username set <username>`. Then you can use just `[p]codewars` instead of `[p]codewars <username>`.

#### Requirements

You can install the requirements seperately:

`[p]pipinstall httpx` - Required for fetching data from Epic Games Store

`[p]pipinstall lxml` - Required for getting avatars of users from GitHub

`[p]pipinstall datetime` - Required for parsing dates

`[p]pipinstall time` - Required for converting ISO 8601 time to unix (epoch) time

##### Credits

[httpx](https://pypi.org/project/httpx/) - HTTPX is a fully featured HTTP client library for Python 3.

[datetime](https://pypi.org/project/DateTime/) - DateTime is a Python module for manipulating dates and times.

[colorthief](https://pypi.org/project/colorthief/) - Color Thief is a Python module for getting the dominant color or a representative color palette from an image.

[lxml](https://pypi.org/project/lxml/) - lxml is a Pythonic, mature binding for the libxml2 and libxslt libraries.

[time](https://docs.python.org/3/library/time.html) - This module provides various functions to manipulate time values.

[menu.py](https://docs.discord.red/en/stable/_modules/redbot/core/utils/menus.html>) - There is a menu in this cog. I edited the original menu from Red Discord Bot.

## Contact

If you have any problem or if you want to improve my cogs, feel free to use issue or pull requests!
