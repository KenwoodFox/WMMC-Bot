# WMMC
# Do cool things like track stats!


import discord
import logging


from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands


class StatTracker(commands.Cog, name="StatTacker"):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(StatTracker(bot))
