# WMMC

import discord
import logging

from datetime import datetime, date

from discord import app_commands
from discord.ext import commands
from utilities.csv_backend import (
    get_row,
    update_user_data,
    autocomplete_users,
    get_backend_path,
    get_users,
    get_overview,
)


@app_commands.autocomplete()
async def autocomplete_users(interaction: discord.Interaction, current: str):
    users = get_users()
    return [app_commands.Choice(name=user[0], value=str(user[1])) for user in users]


class AdminCog(commands.Cog, name="AdminTools"):
    def __init__(self, bot):
        self.bot = bot

        # Consts
        self.base_price = 30

    @app_commands.command(name="register_member")
    @app_commands.checks.has_role("Admin")
    @app_commands.describe(
        user="The user to register",
        real_name="Real name of the member",
        honorary="Is the member honorary? Yes or No",
    )
    async def register_member(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        real_name: str,
        honorary: str,
    ):
        honorary_status = honorary.lower() == "yes"
        update_user_data(
            user.id,
            {
                "discordUsername": user.name,
                "realName": real_name,
                "honorary": honorary_status,
            },
        )
        await interaction.response.send_message(
            f"User {user.display_name} registered successfully as {'honorary' if honorary_status else 'regular'} member.",
            ephemeral=True,
        )

    @app_commands.command(name="dues")
    @app_commands.checks.has_role("Admin")
    @app_commands.describe(user="User to update dues for", amount="Amount paid")
    @app_commands.autocomplete(user=autocomplete_users)
    async def dues(self, interaction: discord.Interaction, user: str, amount: float):
        # The current year
        current_year = str(datetime.now().year)

        update_user_data(
            user,  # User ID
            {current_year: amount},  # Just updating the amount for this year
        )

        await interaction.response.send_message(f"Updated dues.", ephemeral=True)

    def member_since(self, _id: int):
        """Returns the year as an int, that a user first was recorded"""

        current_year = str(datetime.now().year)
        member_data = get_row(_id)

        if member_data:
            # Iterate to find how long they've been a member
            member_since = int(current_year)
            for v in member_data.keys():
                try:
                    year = int(v)
                    if year > 2021:
                        if len(member_data[v]) > 0:
                            member_since = min(member_since, year)
                except ValueError:
                    pass

            return member_since
        else:
            return None

    def is_first_year(self, _id: int) -> bool:
        """True if this is a member's first year"""

        current_year = int(datetime.now().year)
        first_year = self.member_since(_id)  # The first year

        return current_year == first_year

    @app_commands.command(name="my_member_status")
    async def my_member_status(self, interaction: discord.Interaction):
        """
        A badge to show your member status!
        """

        member_data = get_row(interaction.user.id)
        await interaction.response.defer()

        if member_data:
            # The current year
            current_year = str(datetime.now().year)
            # Name
            name = member_data.get("realName", "...")
            # Paid and Dues
            paid, due = self.remaining_dues(interaction.user.id)
            # If they're an honrary member
            honorary = member_data.get("honorary", "False") == "True"

            color = (
                discord.Color.gold()
                if honorary
                else (discord.Color.green() if paid >= due else discord.Color.red())
            )
            embed = discord.Embed(title="Membership Status", color=color)
            embed.add_field(name="Name", value=name, inline=True)
            embed.add_field(
                name="Member Since",
                value=self.member_since(interaction.user.id),
                inline=False,
            )
            if honorary:
                embed.add_field(
                    name="Honorary Member",
                    value="Yes" if honorary else "No",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="Paid This Year",
                    value=f"${paid:.2f}/${due:.2f}",
                    inline=False,
                )

            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("Member data not found.", ephemeral=True)

    @app_commands.command(name="member_overview")
    @app_commands.checks.has_role("Admin")
    async def member_overview(self, interaction: discord.Interaction):
        """Get a quick overview of everyone in the club"""
        await interaction.response.defer()
        await interaction.followup.send(get_overview())

    @app_commands.command(name="get_raw_member_data")
    @app_commands.checks.has_role("Admin")
    async def get_raw_member_data(self, interaction: discord.Interaction):
        """Send the raw CSV data file."""
        await interaction.response.send_message(file=discord.File(get_backend_path()))

    def remaining_dues(self, _id: int) -> (float, float):
        today = date.today()
        current_year = str(today.year)

        # Get the number of remaining months (including the current month)
        remaining_months = 12 - today.month + 1  # +1 to include the current month
        prorated_dues = (self.base_price / 12) * remaining_months

        # Get the member data for the user running the command
        member_data = get_row(_id)
        logging.info(f"Member data was {member_data}")

        if member_data:
            # Skip if honorary
            if member_data.get("honorary", "False") == "True":
                return (0, 0)  # For freeee

            try:
                amount_paid = float(member_data.get(current_year, "0"))
            except ValueError:
                logging.error(f"Aaa got y2k bug moment, inserting 0")
                amount_paid=0
            logging.info(f"current year {amount_paid}")

            # Calculate remaining dues
            if self.is_first_year(_id):
                remaining_dues = max(0, prorated_dues - amount_paid)
                return amount_paid, prorated_dues
            else:
                return amount_paid, self.base_price
        else:
            return (None, None)

    @app_commands.command(name="calculate_remaining_dues")
    async def calculate_remaining_dues(self, interaction: discord.Interaction):
        """Calculate your dues for this year (thank you Apollo)"""

        await interaction.response.defer()

        try:
            paid, due = self.remaining_dues(interaction.user.id)
            logging.info(f"Paid {paid}, due {due} for user {interaction.user}")

            if paid == None or due == None:
                await interaction.followup.send(
                    "Your membership data was not found.", ephemeral=True
                )
                return
            elif paid >= due and due == self.base_price:
                await interaction.followup.send(
                    f"You're a returning member and paid for this year! ${paid:.2f}/${due:.2f}",
                    ephemeral=True,
                )
            elif paid >= due:
                await interaction.followup.send(
                    f"You're paid for this year! ${paid:.2f}/${due:.2f}",
                    ephemeral=True,
                )
            elif paid < due and paid != 0:
                await interaction.followup.send(
                    f"You're still missing a portion of your payment${paid:.2f}/${due:.2f}",
                    ephemeral=True,
                )

            elif paid < due and due < self.base_price:
                await interaction.followup.send(
                    f"You only need to pay dues on the remaining part of the year ${paid:.2f}/${due:.2f}",
                    ephemeral=True,
                )
            elif paid < due and due == self.base_price:
                await interaction.followup.send(
                    f"You need to pay full dues for this year. ${paid:.2f}/${due:.2f}",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "Some other dues condition! Speak to an admin!", ephemeral=True
                )
        except Exception as e:
            await interaction.followup.send(
                f"There was some other error! {e}", ephemeral=True
            )
            raise e


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
