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
        "League of Legends",
        "CS:2",
        "Hearthstone",
        "Geoguessr",
        "Minecraft",
        "Civ VI",
        "With your feelings😈",
        "The Game",
        "Yakuza 0",
        "Among Us",
        "in OSM 2024",
        "Cyberpunk 2077",
        "Stuble Guys",
        "in Biweeklies",
    ]
    # moreCommonStatus = "signup to AG CS2 tournament"
    # for _ in range(10):
    #    status.append(moreCommonStatus)
    await client.change_presence(activity=discord.Game(choice(status)))


@client.event
async def on_ready():
    change_status.start()
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
