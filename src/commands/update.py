import discord
from discord.ext import commands
from utils.utils import get_rs_username, get_ehb, get_total_level
import config
import sqlite3
import os

from dotenv import load_dotenv
load_dotenv()

# SQL
db_path = os.environ.get('DB_PATH')
db_conn = sqlite3.connect(db_path)
class UpdateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_user_role(self, ctx, rs_username):
        ehb_value = get_ehb(rs_username)
        total_level = get_total_level(rs_username)

        for ehb_range, role_name in config.EHB_ROLES.items():
            if ehb_value >= ehb_range.start:
                return discord.utils.get(ctx.guild.roles, name=role_name)

        for level_range, role_name in config.LEVEL_ROLES.items():
            if total_level >= level_range.start:
                return discord.utils.get(ctx.guild.roles, name=role_name)

        return None

    async def update_user_role(self, ctx):
        # Get the linked RS username for the user
        user_id = ctx.author.id
        rs_username = get_rs_username(user_id)
            
        # Get the users role
        user_role = await self.get_user_role(rs_username)

        # Remove any existing roles
        await self.remove_old_roles(ctx, user_role)

        # Assign the new role
        new_role_obj = discord.utils.get(ctx.guild.roles, name=user_role)
        await ctx.author.add_roles(new_role_obj)

        # Send success message
        await ctx.send(f"Your role has been updated to {new_role_obj.name}")

    async def remove_old_roles(self, ctx, user_role):
        roles_to_remove = (discord.utils.get(ctx.member.guild.roles, name=role) for role in
                    set(config.LEVEL_ROLES.values()) | set(config.EHB_ROLES.values()) if role != user_role.name)
        await ctx.member.remove_roles(*(role for role in roles_to_remove if role))

    async def is_linked_user(self, ctx):
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM user_links WHERE discord_id = ?", (ctx.author.id,))
        link = cursor.fetchone()
        cursor.close()

        if link is None:
            await ctx.send("You are not linked to any RuneScape account.")
            return False

        return True

    @commands.command(name="update")
    async def update(self, ctx):
        if self.is_linked_user(ctx):
            return
        await self.update_user_role(ctx)