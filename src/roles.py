# roles.py

import discord
import rs_utils
import config

async def on_message(message, guild, db_conn):
    if message.content.startswith("!update"):
        await update_user_roles(guild, db_conn)

async def update_user_role(message, guild):
    # Get the linked RS username for the user
    user_id = message.author.id

    # Get the user's linked RS username
    row = rs_utils.get_rs_username

    if not row:
        # The user doesn't have a linked RS account
        print(f"User {user_id} does not have a linked RS account")
        await message.channel.send("You don't have a linked RS account. Use `!link <username>` to link your account.")
        return

    # The user has a linked RS account
    username = row[0]

    # Get the user's total level from the hiscores
    total_level = rs_utils.get_total_level(username)

    # Check the user's EHB
    ehb_value = rs_utils.get_ehb(username)

    for ehb_range, role_name in config.EHB_ROLES.items():
        if ehb_value >= ehb_range.start:
            user_role = role_name
            break

    # If no EHB role was assigned, assign the appropriate level role
    if "user_role" not in locals():
        for level_range, role_name in config.LEVEL_ROLES.items():
            if total_level >= level_range.start:
                user_role = role_name
                break

    if "user_role" not in locals():
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
    roles_to_remove = [discord.utils.get(guild.roles, name=role) for role in list(config.LEVEL_ROLES.values()) + list(config.EHB_ROLES.values()) if role != user_role]
    roles_to_remove = [role for role in roles_to_remove if role is not None] # filter out None values
    await member.remove_roles(*roles_to_remove)

    # Assign the new role
    new_role_obj = discord.utils.get(guild.roles, name=user_role)
    await member.add_roles(new_role_obj)

    # Send success message
    await message.channel.send(f"Your role has been updated to {new_role_obj.name}")

async def update_user_roles(guild, db_conn):
    cursor = db_conn.cursor()
    cursor.execute("SELECT discord_id, rs_username FROM user_links")
    rows = cursor.fetchall()
    cursor.close()

    for discord_id, rs_username in rows:
        member = await guild.fetch_member(discord_id)
        if member is None:
            continue

        ehb_value = rs_utils.get_ehb(rs_username)
        total_level = rs_utils.get_total_level(rs_username)

        user_role = None
        for ehb_range, role_name in config.EHB_ROLES.items():
            if ehb_value >= ehb_range.start:
                user_role = role_name
                break

        if not user_role:
            for level_range, role_name in config.LEVEL_ROLES.items():
                if total_level >= level_range.start:
                    user_role = role_name
                    break

        if not user_role:
            continue

        current_roles = {role.name for role in member.roles}
        if user_role in current_roles:
            continue

        # Remove any existing roles
        roles_to_remove = [discord.utils.get(guild.roles, name=role) for role in list(config.LEVEL_ROLES.values()) + list(config.EHB_ROLES.values()) if role != user_role]
        roles_to_remove = [role for role in roles_to_remove if role is not None] # filter out None values
        await member.remove_roles(*roles_to_remove)

        new_role_obj = discord.utils.get(guild.roles, name=user_role)
        await member.add_roles(new_role_obj)

    print("User roles have been updated")