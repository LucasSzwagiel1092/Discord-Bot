# link.py

import sqlite3
from osrs_api import Hiscores

async def on_message(message, db_conn):
    if message.content.startswith("!link"):
        await link_account(message, db_conn)
    elif message.content.startswith("!unlink"):
        await unlink_account(message, db_conn)

async def link_account(message, db_conn):
    # Parse the user's Runescape username from the message
    args = message.content.split()
    if len(args) < 2:
        await message.channel.send("Please enter a RuneScape username to link with your account.")
        return
    username = " ".join(args[1:])

    # Check if the username is already linked to a Discord account
    cursor = db_conn.cursor()
    cursor.execute("SELECT discord_id FROM user_links WHERE rs_username = ?", (username,))
    row = cursor.fetchone()
    cursor.close()

    if row is not None:
        # The username is already linked to a Discord account
        linked_user = message.guild.get_member(row[0])
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
            
async def unlink_account(message, db_conn):
    cursor = db_conn.cursor()
    cursor.execute("DELETE FROM user_links WHERE discord_id = ?", (message.author.id,))
    db_conn.commit()
    cursor.close()

    await message.channel.send(f"Your Discord account has been unlinked from your Runescape account.")

def is_valid_rs_account(username):
    try:
        Hiscores(username)
        return True
    except Exception as e:
        if "_is_bad_username" in str(e):
            return False
        else:
            raise e