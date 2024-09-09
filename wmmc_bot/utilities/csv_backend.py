import csv
from datetime import datetime
import os

backend_path = "/backend/wmmc_registration.csv"


def get_backend_path():
    return backend_path


def load_csv_data():
    """Load data from the CSV file."""
    with open(backend_path, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader), reader.fieldnames


def save_csv_data(data, fieldnames):
    """Save data to the CSV file, adding new year columns if necessary."""
    with open(backend_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def init_backend():
    """Ensure the backend CSV exists and is initialized properly."""
    if not os.path.exists(backend_path):
        with open(backend_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "discordID",
                    "discordUsername",
                    "realName",
                    "honorary",
                    str(datetime.now().year),
                ]
            )


def update_user_data(user_id, updates):
    """Update or add new user data."""
    data, fieldnames = load_csv_data()
    current_year = str(datetime.now().year)
    # Ensure the current year and any specified in updates are in the fieldnames
    required_years = set(updates.keys())
    required_years.add(current_year)
    fieldnames_changed = False

    for year in required_years:
        if year not in fieldnames:
            fieldnames.append(year)
            fieldnames_changed = True

    updated = False
    for row in data:
        if row["discordID"] == str(user_id):
            for key, value in updates.items():
                row[key] = str(int(row.get(key, "0")) + int(value))
            updated = True
            break

    new_user = False
    if not updated:
        new_user_data = {
            "discordID": str(user_id),
            "discordUsername": updates.get("discordUsername", ""),
            "realName": updates.get("realName", ""),
            "honorary": "Yes" if updates.get("honorary", False) else "No",
        }

        # Year Data
        for year in fieldnames:
            if year == current_year:
                new_user_data[year] = "0"

        for key, value in updates.items():
            if key in fieldnames:
                new_user_data[key] = str(value)
        data.append(new_user_data)
        new_user = True

    # Save data if there were changes to fieldnames or if a new user was added
    if fieldnames_changed or updated or new_user:
        save_csv_data(data, fieldnames)


def get_row(discord_id):
    """Retrieve a row by Discord ID."""
    data, _ = load_csv_data()
    for row in data:
        if row["discordID"] == str(discord_id):
            return row
    return None


def get_users():
    """Get all the users"""
    data, _ = load_csv_data()
    ret = []
    for row in data:
        ret.append([row["realName"], row["discordID"]])
    return ret


def get_overview():
    """Format all user data into a readable overview."""
    data, fieldnames = load_csv_data()

    # Remove static fields that are not year-related
    non_year_fields = ["discordID", "discordUsername", "realName", "honorary"]
    year_columns = [field for field in fieldnames if field not in non_year_fields]

    # Start formatting the overview
    overview = "```\nName                 " + "    ".join(year_columns) + "\n"

    for row in data:
        name = row["realName"] or row["discordUsername"]  # Use real name if available
        line = f"{name:<20}"  # Format name with fixed width for alignment

        # Check honorary status and handle yearly contributions
        if row["honorary"] == "Yes":
            line += " " * (len(year_columns) * 6) + "Honorary"
        else:
            for year in year_columns:
                line += f"{row.get(year, '0'):>6}"  # Right-align the contributions or default to 0

        overview += line + "\n"

    overview += "\n```"

    return overview.strip()


def autocomplete_users(current: str):
    """Autocomplete usernames based on current input."""
    data, _ = load_csv_data()
    return [
        {"name": row["discordUsername"], "value": row["discordID"]}
        for row in data
        if current.lower() in row["discordUsername"].lower()
    ]


# Initialize backend when module is loaded
init_backend()
