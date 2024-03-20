# WMMC
# Do cool things like track stats!

import os
import yaml
import discord
import logging


from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands


class StatTracker(commands.Cog, name="StatTacker"):
    def __init__(self, bot):
        self.bot = bot

        # Configure our yaml storage
        self.yamlPath = "/data/stats.yaml"
        if not os.path.exists(self.yamlPath):
            logging.warn("Creating blank file")
            with open(self.yamlPath, "w") as file:
                yaml.dump({}, file)
        else:
            logging.info(f"Found yaml file at {self.yamlPath}")

    @app_commands.command(name="record_stats")
    @app_commands.choices(
        helmet=[
            app_commands.Choice(name="i10", value="i10"),
            app_commands.Choice(name="i90", value="i90"),
        ],
        intercom=[
            app_commands.Choice(name="RT1", value="RT1"),
            app_commands.Choice(name="ST1", value="ST1"),
            app_commands.Choice(name="50R", value="50R"),
            app_commands.Choice(name="50S", value="50S"),
        ],
        training=[
            app_commands.Choice(name="BRC", value="BRC"),
            app_commands.Choice(name="ERC", value="ERC"),
        ],
    )
    async def recordStats(
        self,
        ctx: discord.Interaction,
        helmet: app_commands.Choice[str],
        intercom: app_commands.Choice[str],
        training: app_commands.Choice[str],
        bike_model: str,
    ):
        with open(self.yamlPath, "r") as file:
            cur = yaml.safe_load(file)
            cur.update(
                {
                    ctx.user.global_name: [
                        bike_model,
                        helmet.value,
                        intercom.value,
                        training.value,
                    ]
                }
            )

        with open(self.yamlPath, "w") as file:
            yaml.safe_dump(cur, file)

        await ctx.response.send_message(
            f"Got {bike_model}, {helmet.value} with intercom {intercom.value} and training {training.value}"
        )

    @app_commands.command(name="show_stats")
    async def showData(self, ctx: discord.Interaction):
        pass


async def setup(bot):
    await bot.add_cog(StatTracker(bot))
