# link.py

from discord.ext import commands
import sqlite3
from osrs_api import Hiscores
import os
from dotenv import load_dotenv
import update

load_dotenv()

# SQL
db_path = os.environ.get('DB_PATH')
db_conn = sqlite3.connect(db_path)


class LinkCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.check()
    async def isLinked(self, ctx, username):    
        # Check if the username is already linked to a Discord account
        linked_user_id = db_conn.execute("SELECT discord_id FROM user_links WHERE rs_username = ?", (username,)).fetchone()
        if linked_user_id:
            # The username is already linked to a Discord account
            # Grab the linked accounts discord ID
            linked_user = await ctx.guild.fetch_member(linked_user_id[0])
            
            # Check if the user is still a discord member of the server
            if linked_user:
                await ctx.send(
                    f"The RuneScape account {username} is already linked to the Discord account {linked_user.mention}. "
                    "Please contact an administrator if you believe there is an error."
                    )
            else:
                await ctx.send(
                    f"The RuneScape account {username} is already linked to a Discord account, "
                    "but that account no longer exists on this server. "
                    "Please contact an administrator if you believe there is an error."
                    )
    def isValidRuneScapeAccount(self, username):
        try:
            Hiscores(username)
            return True
        except Exception as e:
            if "Unable to find" in str(e):
                return False
            else:
                raise e

    @commands.command()
    async def link(self, ctx, username):
        user = ctx.author
        await ctx.send(f"Hello, {user.mention}!")
