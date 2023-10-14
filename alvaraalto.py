from random import choice
import discord
from discord.ext import tasks
from src.setup import *
from src.commands import *
from src.gamequeue import *
from src.leaderboard import *


@tasks.loop(seconds=1800)
async def change_status():
    status = [
        "Vibing 8)",
        "😀",
        "😃",
        "😄",
        "😅",
        "🤣",
        "😇",
        "down bad😔",
        "tilted🤬",
        "Molding some glass",
        "Looking at your #grades👀",
        "👨🏻‍🎓",
        "Gamin'",
        "League of Legends",
        "Rocket League",
        "CS:GO",
        "Hearthstone",
        "Browser games",
        "Minecraft",
        "Civ VI",
        "With your feelings😈",
        "The Game",
    ]
    await client.change_presence(activity=discord.Game(choice(status)))


@client.event
async def on_ready():
    # client.tree.copy_global_to(guild=getGuild())
    await client.tree.sync()
    print("Bot is ready.")


@client.event
async def on_member_join(member: discord.Member):
    guild = getGuild()
    welcome_channel = guild.get_channel(805886391853514812)
    mbed = discord.Embed(
        title="Welcome {}!".format(member.name),
        description="Welcome to the Aalto gamers Discord server!\nHead over to the #roles channel to tell us what games you play and want roles for.\nAnd again, a warm welcome to you!",
        color=0xFF4500,
    )
    await welcome_channel.send(f"Welcome to the server {member.mention} 🥳")  # type: ignore
    await member.send(embed=mbed)


client.run(CLIENT_SECRET)
