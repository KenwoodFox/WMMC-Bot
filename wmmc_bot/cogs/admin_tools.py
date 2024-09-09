# WMMC

import discord
import logging

from datetime import datetime

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

    @app_commands.command(name="register_user")
    @app_commands.checks.has_role("Admin")
    @app_commands.describe(
        user="The user to register",
        real_name="Real name of the member",
        honorary="Is the member honorary? Yes or No",
    )
    async def register_user(
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
    async def dues(self, interaction: discord.Interaction, user: str, amount: int):
        # The current year
        current_year = str(datetime.now().year)

        update_user_data(
            user,  # User ID
            {current_year: amount},  # Just updating the amount for this year
        )

        await interaction.response.send_message(f"Updated dues.", ephemeral=True)

    @app_commands.command(name="status")
    async def status(self, interaction: discord.Interaction):
        member_data = get_row(interaction.user.id)

        if member_data:
            # The current year
            current_year = str(datetime.now().year)
            # Name
            name = member_data.get("realName", "...")
            # If they're paid for this year
            paid = member_data.get(current_year, "0") != "0"
            # If they're an honrary member
            honorary = member_data.get("honorary", "No") == "Yes"

            # Iterate to find how long they've been a member
            member_since = current_year
            for v in member_data.keys():
                try:
                    year = int(v)
                    if year > 2021:
                        if len(member_data.get(year, "")) > 0:
                            member_since = min(member_since, year)
                except ValueError:
                    pass

            color = (
                discord.Color.gold()
                if honorary
                else (discord.Color.green() if paid else discord.Color.red())
            )
            embed = discord.Embed(title="Membership Status", color=color)
            embed.add_field(name="Name", value=name, inline=True)
            embed.add_field(name="Member Since", value=member_since, inline=False)
            if honorary:
                embed.add_field(
                    name="Honorary Member",
                    value="Yes" if honorary else "No",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="Paid This Year", value="Yes" if paid else "No", inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "Member data not found.", ephemeral=True
            )

    @app_commands.command(name="overview")
    @app_commands.checks.has_role("Admin")
    async def overview(self, interaction: discord.Interaction):
        """Get a quick overview of everyone in the club"""
        await interaction.response.send_message(get_overview())

    @app_commands.command(name="get_raw_data")
    @app_commands.checks.has_role("Admin")
    async def get_raw_data(self, interaction: discord.Interaction):
        """Send the raw CSV data file."""
        await interaction.response.send_message(file=discord.File(get_backend_path()))


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
