import discord
from discord.ext import commands
import traceback
import os

env = {}
filePath = os.path.join(os.path.dirname(__file__), "../.env")
with open(filePath) as f:
    for line in f:
        if line.startswith("#") or not line.strip():
            continue
        key, value = line.strip().split("=", 1)
        env[key] = value

CLIENT_SECRET = env["DISCORD_TOKEN"]
GITHUB_TOKEN = env["GITHUB_TOKEN"]
IS_DEV_MODE = "DEVELOPMENT" in env

intents = discord.Intents.all()

client = commands.Bot(command_prefix="!", intents=intents)


def getGuild() -> discord.Guild:
    return client.get_guild(1064512464353509407 if IS_DEV_MODE else 273889488520871946)  # type: ignore


roleMessageId = 1066479093387886713 if IS_DEV_MODE else 1066493823628361919
roleChannelId = 1065631803425169639 if IS_DEV_MODE else 805942507250515989
errorMessageChannnelId = 1066495980641460224 if IS_DEV_MODE else 1066495898777034824


async def sendErrorMessage(message):
    channel = client.get_channel(errorMessageChannnelId)
    await channel.send(message)  # type: ignore


async def traceErrorAndSendErrorMessage():
    await sendErrorMessage(traceback.format_exc())
