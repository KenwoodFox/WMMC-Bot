# 2023, Fops Bot
# MIT License


import discord
import logging
import subprocess


from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands


class CameraCog(commands.Cog, name="Snap"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="camera")
    @app_commands.choices(
        camera=[
            app_commands.Choice(name="Barn", value="barn"),
        ]
    )
    async def snapCommand(
        self, ctx: discord.Interaction, camera: app_commands.Choice[str]
    ):
        logging.info(
            f"Processing request for {ctx.user.name}, request is {camera.value}"
        )
        if camera.value == "barn":
            await ctx.response.defer()  # This might take a bit

            # Extract frame
            subprocess.run(
                f"ffmpeg -y -i rtsp://10.85.1.31/ucast/11 -frames:v 1 -q:v 2 /tmp/{camera.value}.png",
                shell=True,
            )
            imageFile = discord.File(f"/tmp/{camera.value}.png")

            await ctx.followup.send(file=imageFile)
        else:
            await ctx.response.send_message("Sorry! There was an error!")


async def setup(bot):
    await bot.add_cog(CameraCog(bot))
