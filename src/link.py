# link.py

import sqlite3
from osrs_api import Hiscores
import os
from dotenv import load_dotenv
import update

load_dotenv()

# SQL
db_path = os.environ.get('DB_PATH')
db_conn = sqlite3.connect(db_path)

async def on_message(message):
    if message.content.startswith("!link "):
        args = message.content.split()
        if len(args) == 2:
            await link_account(message)
        elif len(args) == 3 or len(args) == 4:
            if message.mentions:
                await admin_link_account(message)
            else:
                await link_account(message)
        else:
            await message.channel.send("Invalid command. Please use `!link <RuneScape username>` or `!link <@user> <RuneScape username>`")
    elif message.content.startswith("!unlink "):
        args = message.content.split()
        if len(args) < 2:
            await message.channel.send("Please enter a RuneScape username to unlink from your account.")
            return
        rs_username = " ".join(args[1:])
        await unlink_rs_username(message, rs_username)
    elif message.content == "!link":
        await message.channel.send("Please enter a RuneScape username to link with your account.")
    elif message.content == "!unlink":
        await unlink_discord_account(message)


async def link_account(message):
    # Get the user's desired RuneScape username from the message
    args = message.content.split()
    if len(args) < 2:
        await message.channel.send("Please enter a RuneScape username to link with your account.")
        return
    username = " ".join(args[1:])

    # Check if the username is already linked to a Discord account
    linked_user_id = db_conn.execute("SELECT discord_id FROM user_links WHERE rs_username = ?", (username,)).fetchone()
    if linked_user_id:
        # The username is already linked to a Discord account
        linked_user = await message.guild.fetch_member(linked_user_id[0])
        if linked_user:
            await message.channel.send(f"The RuneScape account {username} is already linked to the Discord account {linked_user.mention}. Please contact an administrator if you believe there is an error.")
        else:
            await message.channel.send(f"The RuneScape account {username} is already linked to a Discord account, but that account no longer exists on this server. Please contact an administrator if you believe there is an error.")
        return

    # Check if the username is a valid RuneScape account
    if not is_valid_rs_account(username):
        await message.channel.send(f"The account {username} is not on the highscores.")
        return

    # Check if the user is already linked to a different RuneScape account
    current_rs_username = db_conn.execute("SELECT rs_username FROM user_links WHERE discord_id = ?", (message.author.id,)).fetchone()
    if current_rs_username:
        await message.channel.send(f"Your Discord account is already linked to the RuneScape account {current_rs_username[0]}. Please use the `!unlink` command to unlink your account first.")
        return

    # Store the link between Discord user ID and RuneScape username in the database
    db_conn.execute("INSERT INTO user_links (discord_id, rs_username) VALUES (?, ?)", (message.author.id, username))
    db_conn.commit()

    # Send a confirmation message to the user
    await message.channel.send(f"Your Discord account has been linked to the RuneScape account {username}.")

async def admin_link_account(message):
    # Check if the user is an admin
    if not message.author.guild_permissions.administrator:
        await message.channel.send('You do not have permission to use this command.')
        return

    # Parse the Discord user and RuneScape username from the message
    args = message.content.split()
    if len(args) < 3:
        await message.channel.send("Please provide a Discord user and a RuneScape username to link.")
        return

    # Find the Discord user object
    discord_user = message.mentions[0]
    if discord_user is None:
        await message.channel.send("Please provide a valid Discord user.")
        return

    # Get the RuneScape username
    if args[2].startswith('"') and args[-1].endswith('"'):
        username = " ".join(args[2:])
        username = username[1:-1]
    else:
        username = args[2]

    # Check if the username is already linked to a Discord account
    cursor = db_conn.cursor()
    cursor.execute("SELECT discord_id FROM user_links WHERE rs_username = ?", (username,))
    row = cursor.fetchone()
    cursor.close()

    if row is not None:
        # The username is already linked to a Discord account
        linked_user = await message.guild.fetch_member(row[0])
        if linked_user:
            await message.channel.send(f"The Runescape account {username} is already linked to the Discord account {linked_user.mention}. Please contact an administrator if you believe there is an error.")
        else:
            await message.channel.send(f"The Runescape account {username} is already linked to a Discord account, but that account no longer exists on this server. Please contact an administrator if you believe there is an error.")
    elif not is_valid_rs_account(username):
        # The username is not a valid Runescape account
        await message.channel.send(f"The account {username} is not on the highscores.")
    else:
        # Check if the Discord account is already linked to a RuneScape account
        cursor = db_conn.cursor()
        cursor.execute("SELECT rs_username FROM user_links WHERE discord_id = ?", (discord_user.id,))
        row = cursor.fetchone()
        cursor.close()

        if row is not None:
            await message.channel.send(f"The Discord account {discord_user.mention} is already linked to the RuneScape account {row[0]}.")
        else:
            # Store the link between Discord user ID and RuneScape username in the database
            cursor = db_conn.cursor()
            cursor.execute("INSERT INTO user_links (discord_id, rs_username) VALUES (?, ?)", (discord_user.id, username))
            db_conn.commit()
            cursor.close()

        # Send a confirmation message to the admin and the linked user
        await message.channel.send(f"The Discord account {discord_user.mention} has been linked to the RuneScape account {username}.")
        await discord_user.send(f"Your Discord account has been linked to the RuneScape account {username}.")

async def unlink_discord_account(message):
    # Remove the link between the Discord user ID and the RuneScape username
    cursor = db_conn.cursor()
    cursor.execute("DELETE FROM user_links WHERE discord_id = ?", (message.author.id,))
    db_conn.commit()
    cursor.close()

    await message.channel.send("Your Discord account has been unlinked from your RuneScape account.")

async def unlink_rs_username(message, rs_username):
    # Check if the user is an admin
    if not message.author.guild_permissions.administrator:
        await message.channel.send('You do not have permission to use this command.')
        return

    cursor = db_conn.cursor()
    cursor.execute("DELETE FROM user_links WHERE discord_id = ? AND rs_username = ?", (message.author.id, rs_username))
    db_conn.commit()
    cursor.close()

    await message.channel.send(f"The Discord account {message.author.mention} has been unlinked from the Runescape account {rs_username}.")

def is_valid_rs_account(username):
    try:
        Hiscores(username)
        return True
    except Exception as e:
        if "Unable to find" in str(e):
            return False
        else:
            raise e