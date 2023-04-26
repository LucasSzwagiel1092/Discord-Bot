# update.py

import sqlite3
import discord
import rs_utils
import config
import os
from dotenv import load_dotenv

load_dotenv()

# SQL
db_path = os.environ.get('DB_PATH')
db_conn = sqlite3.connect(db_path)

async def on_message(message, guild):
    if message.content == "!update" and message.author.guild_permissions.administrator:
        update_channel = discord.utils.get(guild.channels, id=1100894937614143612)
        await update_user_roles(guild, update_channel)
        await message.channel.send("All users roles have been updated")

async def update_user_role(message, guild):
    # Get the linked RS username for the user
    user_id = message.author.id
    rs_username_row = rs_utils.get_rs_username(user_id)

    # Check if the user has a linked RS account
    if not rs_username_row:
        print(f"User {user_id} does not have a linked RS account")
        await message.channel.send("You don't have a linked RS account. Use `!link <username>` to link your account.")
        return
        
    # Get the users role
    rs_username = rs_username_row[0]
    user_role = await get_user_role(rs_username, guild)

    # Remove any existing roles
    await remove_old_roles(user_id, user_role)

    # Assign the new role
    new_role_obj = discord.utils.get(guild.roles, name=user_role)
    await user_id.add_roles(new_role_obj)

    # Send success message
    await message.channel.send(f"Your role has been updated to {new_role_obj.name}")

async def update_user_roles(guild, update_channel):
    updated_users = []

    cursor = db_conn.cursor()
    cursor.execute("SELECT discord_id, rs_username FROM user_links")
    rows = cursor.fetchall()
    cursor.close()

    for discord_id, rs_username in rows:
        member = await guild.fetch_member(discord_id)
        if not member:
            continue

        user_role = await get_user_role(guild, rs_username)
        if not user_role:
            continue

        current_roles = {role.name for role in member.roles}
        if user_role.name in current_roles:
            continue

        await remove_old_roles(member, user_role)
        await member.add_roles(user_role)

        # Add the user and new role to the updated list
        updated_users.append(f"{rs_username} - {user_role.name}")

    # Output the updated users and their new role in the update channel
    if updated_users:
        await update_channel.send(f"The following users have had their roles updated: {', '.join(updated_users)}")


async def get_user_role(guild, rs_username):
    ehb_value = rs_utils.get_ehb(rs_username)
    total_level = rs_utils.get_total_level(rs_username)

    for ehb_range, role_name in config.EHB_ROLES.items():
        if ehb_value >= ehb_range.start:
            return discord.utils.get(guild.roles, name=role_name)

    for level_range, role_name in config.LEVEL_ROLES.items():
        if total_level >= level_range.start:
            return discord.utils.get(guild.roles, name=role_name)

    return None


async def remove_old_roles(member, user_role):
    roles_to_remove = (discord.utils.get(member.guild.roles, name=role) for role in
                   set(config.LEVEL_ROLES.values()) | set(config.EHB_ROLES.values()) if role != user_role.name)
    await member.remove_roles(*(role for role in roles_to_remove if role))