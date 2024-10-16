import discord
from discord.ext import commands
import traceback
import os



CLIENT_SECRET = os.getenv("DISCORD_TOKEN", None)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
IS_DEV_MODE = os.getenv("DEVELOPMENT", False)
if not CLIENT_SECRET:
    raise("Discord token not found from env")

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
