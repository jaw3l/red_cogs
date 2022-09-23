# Repository Name

Description of your repository

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

##### Credits

[httpx](https://pypi.org/project/httpx/) - HTTPX is a fully featured HTTP client library for Python 3.
[datetime](https://pypi.org/project/DateTime/) - DateTime is a Python module for manipulating dates and times.
[colorthief](https://pypi.org/project/colorthief/) - Color Thief is a Python module for getting the dominant color or a representative color palette from an image.

## Contact

If you have any problem or if you want to improve my cogs, feel free to use issue or pull requests!
