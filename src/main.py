# main.py

import discord

from dotenv import load_dotenv
import os
import link
import update

load_dotenv()

token = os.environ.get('TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)



@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

    # Fetch the guild object inside the on_ready coroutine
    guild = client.guilds[0]
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
    
    await link.on_message(message)
    
    await update.on_message(message, client.get_guild(1095118191916744864))

client.run(token)