# 2023, Fops Bot
# MIT License


import discord
import logging
import asyncio
import pytz
import os
import python_weather


from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands, tasks

from datetime import datetime, timedelta, time, timezone

from utilities.common import seconds_until


class FanclubCog(commands.Cog, name="FanclubCog"):
    def __init__(self, bot):
        self.bot = bot

        # timezone
        self.localtz = pytz.timezone("US/Eastern")

        datapath = "/app/data/data.yaml"

        self.tempList = {}

    def getStat(self, guild: int, addOne=False):
        """
        Tell me how many times a guild has been booped
        """

        if guild not in self.tempList.keys():
            self.tempList[guild] = 1

        if addOne:
            self.tempList[guild] += 1

        return self.tempList[guild]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        logging.info(message)

        # Check for boops!
        boops = ["boop", "boops", "boop'd"]
        if (any(item in message.content for item in boops)) and (
            message.author != self.bot.user
        ):
            logging.debug(f"Boop detected in {message}, guild was {message.guild}")
            await message.reply(f"{self.getStat(message.guild, True)} boops!")


async def setup(bot):
    await bot.add_cog(FanclubCog(bot))
