import discord
from discord.ext import commands
import traceback
import os
from dotenv import load_dotenv

load_dotenv()


CLIENT_SECRET = os.getenv("DISCORD_TOKEN", None)
if not CLIENT_SECRET:
    raise ("Discord token not found from env")

intents = discord.Intents.all()

client = commands.Bot(command_prefix="!", intents=intents)

errorMessageChannnelId = 1066495898777034824


async def sendErrorMessage(message):
    channel = client.get_channel(errorMessageChannnelId)
    await channel.send(message)  # type: ignore


async def traceErrorAndSendErrorMessage():
    await sendErrorMessage(traceback.format_exc())
