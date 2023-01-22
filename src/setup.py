import discord
from discord.ext import commands
import traceback

env = {}
with open(".env") as f:
    for line in f:
        key, value = line.strip().split("=", 1)
        env[key] = value

# Get client secret from .env file
client_secret = env["DISCORD_TOKEN"]
is_dev_mode = "DEVELOPMENT" in env


intents = discord.Intents.all()

client = commands.Bot(command_prefix="!", intents=intents)


def getGuild():
    return client.get_guild(1064512464353509407 if is_dev_mode else 273889488520871946)


roleMessageId = 1066479093387886713 if is_dev_mode else 1066493823628361919
roleChannelId = 1065631803425169639 if is_dev_mode else 805942507250515989
errorMessageChannnelId = 1066495980641460224 if is_dev_mode else 1066495898777034824


async def sendErrorMessage(message):
    channel = client.get_channel(errorMessageChannnelId)
    await channel.send(message)


async def traceErrorAndSendErrorMessage():
    await sendErrorMessage(traceback.format_exc())
