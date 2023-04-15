# This example requires the 'message_content' intent.

import discord
from osrs_api.const import AccountType
from osrs_api import Hiscores
import sqlite3


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# SQL
db_conn = sqlite3.connect("E:/Discord Bot/tables/user_links.db")

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

    # Fetch the guild object inside the on_ready coroutine
    guild = client.get_guild(1095118191916744864)
    if guild is not None:
        print(f"Connected to the guild {guild.name}")
    else:
        print("Failed to connect to guild")

@client.event
async def on_member_join(member):
    # Send a welcome message to the user
    welcome_channel = client.get_channel(1096619103537598486) # replace with the ID of your welcome channel
    await welcome_channel.send(f"Welcome to the server, {member.mention}! To link your Runescape account, enter the command `!link <username>` in this channel.")

# Register RS user to discord account
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!link "):
        # Parse the user's Runescape username from the message
        username = " ".join(message.content.split(" ")[1:])

        # Check if the username is already linked to a Discord account
        cursor = db_conn.cursor()
        cursor.execute("SELECT discord_id FROM user_links WHERE rs_username = ?", (username,))
        row = cursor.fetchone()
        cursor.close()

        if row is not None:
            # The username is already linked to a Discord account
            linked_user = client.get_user(row[0])
            await message.channel.send(f"The Runescape account {username} is already linked to the Discord account {linked_user.mention}. Please contact an administrator if you believe there is an error.")
        elif not is_valid_rs_account(username):
            # The username is not a valid Runescape account
            await message.channel.send(f"The account {username} does not exist. Please check your spelling or create a new account if you haven't already.")
        else:
            # Check if the user is already linked to a different RuneScape account
            cursor = db_conn.cursor()
            cursor.execute("SELECT rs_username FROM user_links WHERE discord_id = ?", (message.author.id,))
            row = cursor.fetchone()
            cursor.close()

            if row is not None:
                # The user is already linked to a different RuneScape account
                await message.channel.send(f"Your Discord account is already linked to the RuneScape account {row[0]}. Please use the `!unlink` command to unlink your account first.")
            else:
                # Store the link between Discord user ID and RuneScape username in the database
                cursor = db_conn.cursor()
                cursor.execute("INSERT INTO user_links (discord_id, rs_username) VALUES (?, ?)", (message.author.id, username))
                db_conn.commit()
                cursor.close()

                # Send a confirmation message to the user
                await message.channel.send(f"Your Discord account has been linked to the RuneScape account {username}.")


    elif message.content.startswith("!unlink"):
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM user_links WHERE discord_id = ?", (message.author.id,))
        db_conn.commit()
        cursor.close()

        await message.channel.send(f"Your Discord account has been unlinked from your Runescape account.")    
    
    elif message.content.startswith("!update"):
        await update_user_role(message.author.id, message.guild)
        await message.channel.send("Your role has been updated.")

def is_valid_rs_account(username):
    try:
        Hiscores(username)
        return True
    except Exception as e:
        if "_is_bad_username" in str(e):
            return False
        else:
            raise e

async def update_user_role(user_id, guild):
    # Get the linked RS username for the user
    cursor = db_conn.cursor()
    cursor.execute("SELECT rs_username FROM user_links WHERE discord_id = ?", (user_id,))
    row = cursor.fetchone()
    cursor.close()

    if row is not None:
        # The user has a linked RS account
        username = row[0]

        # Get the user's total level from the hiscores
        total_level = Hiscores(username, AccountType.NORMAL).total_level
        print(username)

        # Define a dictionary mapping total levels to Discord roles
        level_roles = {
            range(1, 1250): "Squire",
            range(1250, 1500): "Infantry",
            range(1750, 2000): "Superior",
            range(2000, 9999): "Priest",
        }

        # Find the highest total level in the dictionary that the user's level is greater than or equal to
        user_role = None
        for level_range, role_name in level_roles.items():
            if total_level >= level_range.start:
                user_role = role_name
            else:
                break

        if user_role is not None:
            # Assign the user's new role if it's different from his current one
            member = await guild.fetch_member(user_id)
            if member is not None and user_role not in [role.name for role in member.roles]:
                # Remove any existing roles
                roles_to_remove = [discord.utils.get(guild.roles, name=role) for role in level_roles.values() if role != user_role]
                roles_to_remove = [role for role in roles_to_remove if role is not None] # filter out None values
                await member.remove_roles(*roles_to_remove)

                # Assign the new role
                new_role_obj = discord.utils.get(guild.roles, name=user_role)
                await member.add_roles(new_role_obj)
    else:
        # The user doesn't have a linked RS account
        print(f"User {user_id} does not have a linked RS account")
    
client.run('MTA5NTExMjY1NTAyMDIzMjc0NQ.GIeYjS.s3BXlBs4EPJpDTptqrXBf8yVJeMKGuw2ezR-yc')