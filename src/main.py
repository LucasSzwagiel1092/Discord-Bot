# main.py

import discord
from discord.ext import commands
from commands.link import LinkCog
from commands.update import UpdateCog

from dotenv import load_dotenv
import os

load_dotenv()

token = os.environ.get('TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)



@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

    # Fetch the guild object inside the on_ready coroutine
    guild = bot.guilds[0]
    if guild is not None:
        print(f"Connected to the guild {guild.name}")
    else:
        print("Failed to connect to guild")
        
    await bot.add_cog(LinkCog(bot))
    await bot.add_cog(UpdateCog(bot))

@bot.event
async def on_member_join(member):
    # Send a welcome message to the user
    welcome_channel = bot.get_channel(1096619103537598486) # replace with the ID of your welcome channel
    await welcome_channel.send(f"Welcome to the server, {member.mention}! To link your Runescape account, enter the command `!link <username>` in this channel.")

    

bot.run(token)