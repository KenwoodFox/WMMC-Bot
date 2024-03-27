# WMMC
# Do cool things like track stats!

import os
import discord
import logging
import asyncio

from sqlalchemy import create_engine, Column, Integer, String, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands, tasks

from utilities.common import seconds_until

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

        # Tasks
        self.dailyStats.start()

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
        return [app_commands.Choice(name=v, value=v) for v in ["BRC", "ERC", "None"]]

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

        try:
            # Check if the user already exists in the database
            existing_user = (
                session.query(UserStats).filter_by(id=str(ctx.user.id)).first()
            )

            # If the user exists, update the attributes
            if existing_user:
                await ctx.response.send_message(
                    f"Recording you as an existing user! Bike {bike_model}"
                )
                existing_user.helmet = helmet
                existing_user.model = bike_model
                existing_user.intercom = intercom
                existing_user.mileage = mileage
                existing_user.training = training
            # If the user doesn't exist, create a new one
            else:
                await ctx.response.send_message(
                    f"Recording you as a new user! Bike {bike_model}"
                )
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
        finally:
            session.close()

    @app_commands.command(name="admin_stats")
    @app_commands.autocomplete(helmet=prefetchHelmets)
    @app_commands.autocomplete(training=prefetchTraining)
    @app_commands.autocomplete(intercom=prefetchIntercoms)
    @app_commands.autocomplete(bike_model=prefetchModels)
    @commands.has_role("Admin")
    async def recordStatsAdmin(
        self,
        ctx: discord.Interaction,
        user: discord.Member,
        helmet: str,
        intercom: str,
        training: str,
        bike_model: str,
        mileage: int,
    ):
        session = Session()

        """ Just a copy of the regular recordStats but allows admins to insert UIDs manually """

        try:
            # Check if the user already exists in the database
            existing_user = session.query(UserStats).filter_by(id=str(user.id)).first()

            # If the user exists, update the attributes
            if existing_user:
                await ctx.response.send_message(
                    f"Recording you as an existing user! Bike {bike_model}"
                )
                existing_user.helmet = helmet
                existing_user.model = bike_model
                existing_user.intercom = intercom
                existing_user.mileage = mileage
                existing_user.training = training
            # If the user doesn't exist, create a new one
            else:
                await ctx.response.send_message(
                    f"Recording you as a new user! Bike {bike_model}"
                )
                new_user = UserStats(
                    id=user.id,
                    helmet=helmet,
                    model=bike_model,
                    intercom=intercom,
                    mileage=mileage,
                    training=training,
                )
                session.add(new_user)

            session.commit()
        finally:
            session.close()

    def getRows(self):
        session = Session()
        try:
            # Query the database for users ordered by mileage
            users = session.query(UserStats).order_by(desc(UserStats.mileage)).all()
            return users
        finally:
            session.close()

    def buildStats(self, guild):
        msg = f"```md\n  ===  WMMC Stats!  ===  \n\n{'Member':20}{'Bike':10}{'Helmet':10}{'Intercom':10}{'Training':10}{'Mileage':10}\n"

        for user in self.getRows():
            # Need to fetch local username
            username = "Error"
            try:
                member = guild.get_member(int(user.id))
                username = member.display_name
            except:
                logging.error(f"Error fetching username for {user.id}")
                pass

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

        return msg

    @app_commands.command(name="stats")
    async def showData(self, ctx: discord.Interaction):
        guild = ctx.guild
        await ctx.response.send_message(self.buildStats(guild))

    @tasks.loop(minutes=1)
    async def dailyStats(self):
        logging.info("Scheduling daily stats")

        try:
            wait = seconds_until(7, 10)  # Wait here till 7:10am
            logging.info(f"Waiting {wait:.2f} seconds before running daily stats")
            await asyncio.sleep(wait)
            logging.info("Running now!")

            logging.info("Getting alert channel")
            alert_channel = self.bot.get_channel(
                int(os.environ.get("WEATHER_CHAN_ID", ""))
            )

            logging.info("Getting stats")

            await alert_channel.send(self.buildStats(alert_channel.guild))
        except Exception as e:
            logging.error(f"Error in sending stats! {e}")
        await asyncio.sleep(60)  # So we dont spam


async def setup(bot):
    await bot.add_cog(StatTracker(bot))
