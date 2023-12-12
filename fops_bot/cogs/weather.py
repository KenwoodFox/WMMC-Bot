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

from utilities.common import seconds_until


async def getweather():
    # declare the client. the measuring unit used defaults to the metric system (celcius, km/h, etc.)
    async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
        # fetch a weather forecast from a city
        weather = await client.get("Concord, New Hampshire")

        # returns the current day's forecast temperature (int)
        # print(weather.current.temperature)

        forecast = next(weather.forecasts)

        data = f"""\tJoes Weather Forecast for {forecast.date}\t\n"""
        for hourly in forecast.hourly:
            warn = False
            # Conditions to warn riders
            if hourly.temperature < 40 or hourly.temperature > 105:
                warn = True
                logging.info(f"Temperature ({hourly.temperature}) was out of range")

            if "rain" in hourly.description:
                warn = True
                logging.info(f"Rain detected in {hourly.description}")

            data += f"{hourly.time.strftime('%I %p')} Temperature {hourly.temperature:3}f, {hourly.description:16}\t"

            if warn:
                data += "(!)\n"
            else:
                data += "\n"

        data += f"\nVisibility {weather.current.visibility} miles\n"

        if warn:
            data += "\n (!) Weather conditions may not be favorable for riding. (!)\n"

        data += f"\nVersion {os.environ.get('GIT_COMMIT')}"

        return data


class WeatherCog(commands.Cog, name="WeatherCog"):
    def __init__(self, bot):
        self.bot = bot

        # timezone
        self.localtz = pytz.timezone("US/Eastern")

        # Tasks
        self.alert_channel = self.bot.get_channel(
            int(os.environ.get("WEATHER_CHAN_ID", ""))
        )
        self.weather_alert.start()

    @tasks.loop(minutes=1)
    async def weather_alert(self):
        logging.info("Scheduling weather alert")

        wait = seconds_until(8, 00)  # Wait here till 8am
        logging.info(f"Waiting {wait} before running")
        await asyncio.sleep(wait)
        logging.info("Running now!")

        data = await getweather()
        await self.alert_channel.send(f"```\n{data}\n```")

        await asyncio.sleep(60)  # So we dont spam

    @app_commands.command(name="weather")
    async def version(self, ctx: discord.Interaction):
        """
        Shows you the weather
        """

        data = await getweather()

        await ctx.response.send_message(f"```\n{data}\n```")


async def setup(bot):
    await bot.add_cog(WeatherCog(bot))
