import discord
from discord import app_commands
import random
from .setup import client


@client.tree.command(description="Get your ping to the server.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Taasko kaatu puu ja veti sähköt? Ping: {:d}".format(
            round(client.latency * 1000)
        )
    )


@client.tree.command(
    description="Get a random number between 1 and n. Default n is 100."
)
@app_commands.describe(n="The maximum value of the roll. Defaults to 100.")
async def roll(interaction: discord.Interaction, n: int = 100):
    try:
        end = int(n)
        await interaction.response.send_message(round(random.uniform(1, end)))
    except (ValueError, TypeError, Exception) as _:
        await interaction.response.send_message(round(random.uniform(1, 100)))
