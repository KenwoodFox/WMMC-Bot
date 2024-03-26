# WMMC
# Do cool things like track stats!

import os
import discord
import logging

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands

# Define the SQLAlchemy engine
engine = create_engine("db://postgres_db/database", echo=True)

# Create a session maker
Session = sessionmaker(bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()


# This is the model we'll use to store the stats
class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True)
    helmet = Column(String)
    model = Column(String)
    intercom = Column(String)
    mileage = Column(Integer)
    training = Column(String)


class StatTracker(commands.Cog, name="StatTacker"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="record_stats")
    async def recordStats(
        self,
        ctx: discord.Interaction,
        helmet: str,
        intercom: str,
        training: str,
        bike_model: str,
        mileage: int,
    ):
        with open(self.yamlPath, "r") as file:
            cur = yaml.safe_load(file)
            cur.update(
                {
                    ctx.user.id: [
                        bike_model,
                        helmet,
                        intercom,
                        training,
                        mileage,
                    ]
                }
            )

        with open(self.yamlPath, "w") as file:
            yaml.safe_dump(cur, file)

        await ctx.response.send_message(
            f"Got {bike_model}, {helmet} with intercom {intercom} and training {training}"
        )

    @app_commands.command(name="stats")
    async def showData(self, ctx: discord.Interaction):
        with open(self.yamlPath, "r") as file:
            data = yaml.safe_load(file)

        msg = f"```md\n  ===  WMMC Stats!  ===  \n\n{'Member':20}{'Bike':10}{'Helmet':10}{'Intercom':10}{'Training':10}{'Mileage':10}\n"

        for user in data:
            # Need to fetch local username
            guild = ctx.guild
            member = guild.get_member(int(user))
            username = member.global_name

            # Build a row
            msg += f"{username:20}"
            for stat in data[user]:
                msg += f"{stat:10}"

            # End a row
            msg += "\n"

        msg += "\n```"

        await ctx.response.send_message(msg)


async def setup(bot):
    await bot.add_cog(StatTracker(bot))
