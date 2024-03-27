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
engine = create_engine("postgresql://db/database", echo=True)

# Create a session maker
Session = sessionmaker(bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()


# This is the model we'll use to store the stats
class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(String, primary_key=True)
    helmet = Column(String)
    model = Column(String)
    intercom = Column(String)
    mileage = Column(Integer)
    training = Column(String)


class StatTracker(commands.Cog, name="StatTacker"):
    def __init__(self, bot):
        self.bot = bot

        # Create all
        Base.metadata.create_all(engine)

    async def prefetchHelmets(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Returns a discord selector list of all the previous entries"""

        return [
            app_commands.Choice(name=v, value=v)
            for v in self.get_unique_values("helmet")
        ]

    async def prefetchIntercoms(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Returns a discord selector list of all the previous entries"""

        return [
            app_commands.Choice(name=v, value=v)
            for v in self.get_unique_values("intercom")
        ]

    async def prefetchModels(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Returns a discord selector list of all the previous entries"""

        return [
            app_commands.Choice(name=v, value=v)
            for v in self.get_unique_values("model")
        ]

    async def prefetchTraining(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=v, value=v) for v in ["BRC", "ERC"]]

    def get_unique_values(self, column_name):
        """Return a list of unique values for a particular colum name"""
        session = Session()

        try:
            # Query the database for distinct values of the specified column
            values = session.query(getattr(UserStats, column_name)).distinct().all()
            print(values)
            return [value[0] for value in values]
        finally:
            session.close()

    @app_commands.command(name="record_stats")
    @app_commands.autocomplete(helmet=prefetchHelmets)
    @app_commands.autocomplete(training=prefetchTraining)
    @app_commands.autocomplete(intercom=prefetchIntercoms)
    @app_commands.autocomplete(bike_model=prefetchModels)
    async def recordStats(
        self,
        ctx: discord.Interaction,
        helmet: str,
        intercom: str,
        training: str,
        bike_model: str,
        mileage: int,
    ):
        session = Session()
        new_user = UserStats(
            id=ctx.user.id,
            helmet=helmet,
            model=bike_model,
            intercom=intercom,
            mileage=mileage,
            training=training,
        )
        session.add(new_user)
        session.commit()

        await ctx.response.send_message(
            f"Got {bike_model}, {helmet} with intercom {intercom} and training {training}!\nRun `\stats` to see your position"
        )

    def getRows(self):
        session = Session()
        try:
            # Query the database for users ordered by mileage
            users = session.query(UserStats).order_by(UserStats.mileage).all()
            return users
        finally:
            session.close()

    @app_commands.command(name="stats")
    async def showData(self, ctx: discord.Interaction):
        msg = f"```md\n  ===  WMMC Stats!  ===  \n\n{'Member':20}{'Bike':10}{'Helmet':10}{'Intercom':10}{'Training':10}{'Mileage':10}\n"

        for user in self.getRows():
            # Need to fetch local username
            guild = ctx.guild
            member = guild.get_member(int(user.id))
            username = member.global_name

            # Build a row
            msg += f"{username:20}"
            msg += f"{user.model:10}"
            msg += f"{user.helmet:10}"
            msg += f"{user.intercom:10}"
            msg += f"{user.training:10}"
            msg += f"{user.mileage:10}"

            # End a row
            msg += "\n"

        msg += "\n```"

        await ctx.response.send_message(msg)


async def setup(bot):
    await bot.add_cog(StatTracker(bot))
