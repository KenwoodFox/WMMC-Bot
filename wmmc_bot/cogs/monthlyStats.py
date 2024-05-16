# WMMC
# Addresses #3, monthly stats!

import os
import discord
import logging
import asyncio

from datetime import datetime, timedelta


from sqlalchemy import create_engine, Column, Integer, String, DateTime, desc
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
class MonthlyStatModel(Base):
    __tablename__ = "monthly_stats"

    id = Column(Integer, primary_key=True)

    user_id = Column(String)
    model = Column(String)
    mileage = Column(Integer)
    updated = Column(DateTime, default=datetime.now)


class MonthlyStats(commands.Cog, name="MonthlyStats"):
    def __init__(self, bot):
        self.bot = bot

        # Create all
        Base.metadata.create_all(engine)

        # Persistent storage
        self.old_leaderboard = []

        # Tasks
        # self.dailyStats.start()

    async def prefetchModels(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Returns a discord selector list of all the previous entries"""

        return [
            app_commands.Choice(name=v, value=v)
            for v in self.get_unique_values("model", interaction.user.user_id)
        ]

    def get_unique_values(self, column_name, user_id=None):
        """Return a list of unique values for a particular column name."""
        session = Session()

        logging.info(f"Prefetching for {user_id}, column {column_name}")

        try:
            # Query the database for distinct values of the specified column
            values_query = session.query(
                getattr(MonthlyStatModel, column_name)
            ).distinct()

            # Get the distinct values
            values = [value[0] for value in values_query.all()]

            # If user_id is provided, prioritize the last entered value for that user
            if user_id is not None:
                last_entry = (
                    session.query(getattr(MonthlyStatModel, column_name))
                    .filter_by(user_id=str(user_id))
                    .order_by(MonthlyStatModel.user_id.desc())
                    .first()
                )
                if last_entry:
                    last_value = last_entry[0]
                    # Move the last entered value to the top of the list
                    values = [last_value] + [
                        value for value in values if value != last_value
                    ]

            # print(values)
            return values
        except Exception as e:
            logging.error(e)
        finally:
            session.close()

    # =======
    # Database stuff
    # =======

    def add_entry(self, model: str, mileage: int, user_id: str):
        """
        Add a new entry to the database.
        """
        session = Session()

        try:
            # Check if there are any existing entries for the same user_id and model
            existing_entry = (
                session.query(MonthlyStatModel)
                .filter(
                    MonthlyStatModel.user_id == user_id, MonthlyStatModel.model == model
                )
                .order_by(MonthlyStatModel.updated.desc())
                .first()
            )

            if existing_entry is None or existing_entry.mileage <= mileage:
                new_entry = MonthlyStatModel(
                    model=model, mileage=mileage, user_id=user_id
                )
                session.add(new_entry)
                session.commit()
            else:
                logging.error("Error! Cant roll back!")
                raise Exception("Cannot roll odometer back.")

        except Exception as e:
            print(f"AAAHH ERROR {e}")
            raise e
        finally:
            session.close()

    def get_monthly_mileage(self, user_id: str):
        """
        Get the mileage for the current month for a specific user.
        """
        session = Session()
        current_month = datetime.now().month
        current_year = datetime.now().year
        start_date = datetime(current_year, current_month, 1)
        end_date = start_date + timedelta(days=30)  # Assuming a month is 30 days

        monthly_entries = (
            session.query(MonthlyStatModel)
            .filter(
                MonthlyStatModel.user_id == user_id,
                MonthlyStatModel.updated >= start_date,
                MonthlyStatModel.updated <= end_date,
            )
            .order_by(MonthlyStatModel.updated)
            .all()
        )

        # If there are no entries or only one entry, return 0 mileage
        if not monthly_entries or len(monthly_entries) == 1:
            return 0

        # Get the mileage difference between the first and last entry of the month
        first_entry_mileage = monthly_entries[0].mileage
        last_entry_mileage = monthly_entries[-1].mileage
        total_mileage = last_entry_mileage - first_entry_mileage

        session.close()
        return total_mileage

    def get_raw_leaderboard(self):
        """
        Get the leaderboard for the last month.
        """
        session = Session()
        current_month = datetime.now().month
        current_year = datetime.now().year
        start_date = datetime(current_year, current_month, 1)
        end_date = start_date + timedelta(days=30)  # Assuming a month is 30 days

        monthly_entries = (
            session.query(MonthlyStatModel.user_id, MonthlyStatModel.model)
            .filter(
                MonthlyStatModel.updated >= start_date,
                MonthlyStatModel.updated <= end_date,
            )
            .distinct()
            .all()
        )

        leaderboard = []
        for user_id, model in monthly_entries:
            mileage = self.get_monthly_mileage(user_id)
            leaderboard.append([user_id, model, mileage])

        # Sort the leaderboard based on mileage (descending order)
        leaderboard.sort(key=lambda x: x[2], reverse=True)

        session.close()
        return leaderboard

    def getUsername(self, guild, id):
        username = "Error"
        try:
            member = guild.get_member(int(id))
            username = member.display_name[:18]
        except:
            logging.error(f"Error fetching username for {id}")
        finally:
            return username

    def buildTextLeaderboard(self, _guild, bump=False):
        data = self.get_raw_leaderboard()
        prev_data = self.old_leaderboard

        header = f"```diff\n === Monthly Stats for [] ===\n\n"

        _ret = header

        mismatch = False

        for i, entry in enumerate(data):
            try:
                pd = prev_data[i]
            except IndexError:
                pd = None

            if pd == entry:
                sym = " "
            else:
                if not mismatch:
                    sym = "+"
                    mismatch = True
                else:
                    sym = "-"
            _ret += f"{sym} `{self.getUsername(_guild, entry[0])}\t{entry[1]}\t{entry[2]}`\n"

        if bump:
            self.old_leaderboard = data
        _ret += "```"

        return _ret

    @app_commands.command(name="monthly")
    @app_commands.autocomplete(bike_model=prefetchModels)
    async def monthly(
        self,
        ctx: discord.Interaction,
        bike_model: str,
        mileage: int,
    ):

        await ctx.response.defer()

        await ctx.followup.send(
            f"Recording your entry for {bike_model}, mileage {mileage}.."
        )

        try:
            # Add entry
            self.add_entry(bike_model, mileage, str(ctx.user.id))

            # guild = ctx.guild
            # await ctx.followup.send(self.get_monthly_mileage(str(ctx.user.id)))
            guild = ctx.guild
            await ctx.followup.send(self.buildTextLeaderboard(guild, True))
        except Exception as e:
            await ctx.followup.send(f"There was an error! `{e}`")
            raise e

    @app_commands.command(name="thismonth")
    async def thisMonth(self, ctx: discord.Interaction):
        await ctx.response.defer()
        guild = ctx.guild
        await ctx.followup.send(self.buildTextLeaderboard(guild))


async def setup(bot):
    await bot.add_cog(MonthlyStats(bot))
