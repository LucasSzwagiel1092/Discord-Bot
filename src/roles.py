# roles.py

import discord
from osrs_api import Hiscores
from osrs_api.const import AccountType
import ehb

async def on_message(message, guild, db_conn):
    if message.content.startswith("!update"):
        await update_user_role(message, guild, db_conn)

async def update_user_role(message, guild, db_conn):
    # Get the linked RS username for the user
    user_id = message.author.id

    # Get the user's linked RS username
    cursor = db_conn.cursor()
    cursor.execute("SELECT rs_username FROM user_links WHERE discord_id = ?", (user_id,))
    row = cursor.fetchone()
    cursor.close()

    if not row:
        # The user doesn't have a linked RS account
        print(f"User {user_id} does not have a linked RS account")
        await message.channel.send("You don't have a linked RS account. Use `!link <username>` to link your account.")
        return

    # The user has a linked RS account
    username = row[0]

    # Get the user's total level from the hiscores
    total_level = Hiscores(username, AccountType.NORMAL).total_level
    print(username)

    # Check the user's EHB
    ehb_value = await ehb.get_ehb(username)

    # Define a dictionary mapping total levels to Discord roles
    ehb_roles = {
        range(200, 400): "Knight",
        range(400, 600): "Paladin",
        range(600, 800): "Beast",
        range(800, 1000): "Destroyer",
        range(1000, 9999): "Wrath",
    }

    # Define a dictionary mapping total levels to Discord roles
    level_roles = {
        range(1250, 1500): "Squire",
        range(1500, 1750): "Infantry",
        range(1750, 2000): "Superior",
        range(2000, 3000): "Priest",
    }
    
    # Find the highest total level in the dictionary that the user's level is greater than or equal to
    user_role = None
    for ehb_range, role_name in ehb_roles.items():
        if ehb_value >= ehb_range.start:
                user_role = role_name
        else:

            # Find the highest total level in the dictionary that the user's level is greater than or equal to
            user_role = None
            for level_range, role_name in level_roles.items():
                if total_level >= level_range.start:
                    user_role = role_name
                else:
                    break
    
    if user_role is None:
        # User's level is not high enough for any role
        await message.channel.send("Your level is not high enough for any role")
        return

    # Assign the user's new role if it's different from their current one
    member = await guild.fetch_member(user_id)
    if member is None:
        return

    current_roles = [role.name for role in member.roles]
    if user_role in current_roles:
        await message.channel.send("You already have the correct role")
        return

    # Remove any existing roles
    roles_to_remove = [discord.utils.get(guild.roles, name=role) for role in level_roles.values() if role != user_role]
    roles_to_remove = [role for role in roles_to_remove if role is not None] # filter out None values
    await member.remove_roles(*roles_to_remove)

    # Assign the new role
    new_role_obj = discord.utils.get(guild.roles, name=user_role)
    await member.add_roles(new_role_obj)

    # Send success message
    await message.channel.send(f"Your role has been updated to {new_role_obj.name}")