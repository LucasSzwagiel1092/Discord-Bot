# link.py

from discord.ext import commands

import sqlite3
from osrs_api import Hiscores
import os

from dotenv import load_dotenv
load_dotenv()

# SQL
db_path = os.environ.get('DB_PATH')
db_conn = sqlite3.connect(db_path)


class LinkCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    async def is_valid_runescape_account(self, username):
        try:
            Hiscores(username)
            return True
        except Exception as e:
            if "Unable to find" in str(e):
                raise commands.BadArgument(f"The RuneScape account {username} could not be found. Please make sure the name is correct.")
            else:
                raise commands.BadArgument(f"An error occurred while checking the RuneScape account {username}. Please try again later.")

    async def is_rs_account_linked(self, ctx, username):    
        # Check if the username is already linked to a Discord account
        linked_user_id = db_conn.execute("SELECT discord_id FROM user_links WHERE rs_username = ?", (username,)).fetchone()
        if linked_user_id:
            # The username is already linked to a Discord account
            # Grab the linked accounts discord ID
            linked_user = self.bot.get_user(linked_user_id[0])
            
            # Check if the user is still a discord member of the server
            if linked_user:
                await ctx.send(
                    f"The RuneScape account {username} is already linked to the Discord account {linked_user.mention}. "
                    "Please contact an administrator if you believe there is an error."
                    )
            else:
                db_conn.execute("DELETE FROM user_links WHERE rs_username = ?", (username,))
                db_conn.commit()
                await ctx.send(
                    f"The RuneScape account {username} is already linked to a Discord account, "
                    "but that account no longer exists on this server. "
                    "The old link has been removed. Please contact an administrator if you believe there is an error."
                    )
            return False
        else:
            return True
        
    async def is_unlinked(self, ctx):
        current_rs_username = db_conn.execute("SELECT rs_username FROM user_links WHERE discord_id = ?", (ctx.author.id,)).fetchone()
        if current_rs_username:
            await ctx.send(
                f"Your Discord account is already linked to the RuneScape account {current_rs_username[0]}. "
                "Please use the `!unlink` command to unlink your account first."
            )
            return False
        else:
            return True
        
    async def is_linked_user(self, ctx):
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM user_links WHERE discord_id = ?", (ctx.author.id,))
        link = cursor.fetchone()
        cursor.close()

        if link is None:
            await ctx.send("You are not linked to any RuneScape account.")
            return False

        return True
    
    @commands.command(name="link")
    async def link(self, ctx, *, username):
        if await self.is_valid_runescape_account(username):
            return
        if await self.is_rs_account_linked(ctx, username):
            return
        if await self.is_unlinked(ctx):
            return
        # Store the link between Discord user ID and RuneScape username in the database
        db_conn.execute("INSERT INTO user_links (discord_id, rs_username) VALUES (?, ?)", (ctx.author.id, username))
        db_conn.commit()

        # Send a confirmation message to the user
        await ctx.send(f"Your Discord account has been linked to the RuneScape account {username}.")
    
    @link.error
    async def link_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a RuneScape username to link your account to.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(str(error))
        else:
            await ctx.send(f"An error occurred: {str(error)}")

    @commands.command(name="unlink")
    async def unlink_discord_account(self, ctx):
        if await self.is_linked_user(ctx):
            return
        # Remove the link between the Discord user ID and the RuneScape username
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM user_links WHERE discord_id = ?", (ctx.author.id,))
        db_conn.commit()
        cursor.close()

        await ctx.send("Your Discord account has been unlinked from your RuneScape account.")
