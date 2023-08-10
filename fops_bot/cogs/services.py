# Services cog
# Functions to interact with various services!


import os
import discord
import logging
import requests


from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands, tasks


class servicesCog(commands.Cog, name="Bconsole"):
    def __init__(self, bot):
        self.bot = bot

    def sizeof_fmt(self, num):
        for unit in ("Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"):
            if abs(num) < 1024.0:
                return f"{num:3.1f} {unit}"
            num /= 1024.0
        return f"{num} Bytes"

    @app_commands.command(name="service")
    @app_commands.choices(
        service=[
            app_commands.Choice(name="Nextcloud", value="nc"),
        ]
    )
    async def serviceCommand(
        self, ctx: discord.Interaction, service: app_commands.Choice[str]
    ):
        logging.info(
            f"Processing request for {ctx.user.name}, request is {service.value}"
        )
        if service.value == "nc":
            await ctx.response.defer()  # This might take a bit

            try:
                nc_api = "https://nextcloud.kitsunehosting.net/ocs/v2.php/apps/serverinfo/api/v1/info?format=json"
                resp = requests.get(
                    nc_api, headers={"NC-Token": os.environ.get("NCTOKEN")}
                )
                data = resp.json()
            except Exception as e:
                await ctx.followup.send(
                    f"Ohno! There was an error reaching NC...\n```{e}```"
                )
                return

            embed = discord.Embed(
                title="Nextcloud Stats",
                color=0x76FF26,
            )

            embed.add_field(
                name="Version",
                value=data["ocs"]["data"]["nextcloud"]["system"]["version"],
                inline=False,
            )

            embed.add_field(
                name="Total Files",
                value=data["ocs"]["data"]["nextcloud"]["storage"]["num_files"],
                inline=False,
            )

            embed.add_field(
                name="Database Size",
                value=self.sizeof_fmt(
                    int(data["ocs"]["data"]["server"]["database"]["size"])
                ),
                inline=False,
            )

            embed.add_field(
                name="Users (5m)",
                value=data["ocs"]["data"]["activeUsers"]["last5minutes"],
                inline=True,
            )

            embed.add_field(
                name="Users (1hr)",
                value=data["ocs"]["data"]["activeUsers"]["last1hour"],
                inline=True,
            )

            embed.add_field(
                name="Users (24hr)",
                value=data["ocs"]["data"]["activeUsers"]["last24hours"],
                inline=True,
            )

            embed.set_footer(text=f"Bot Version {self.bot.version}")

            await ctx.followup.send(embed=embed)
        else:
            await ctx.response.send_message("Sorry! Couldn't find that service.")


async def setup(bot):
    await bot.add_cog(servicesCog(bot))
