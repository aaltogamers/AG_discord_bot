import discord
from discord import app_commands
import random
from .setup import client
import os
from mcrcon import MCRcon


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


@client.tree.command(description="Get server owner")
async def owner(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Server owner is: " + str(interaction.guild.owner.name)
    )


@client.tree.command(
    name="whitelist", description="Whitelist a player on the Minecraft server"
)
@app_commands.describe(username="The exact Minecraft username to whitelist")
async def whitelist_player(interaction: discord.Interaction, username: str):
    # Defer the response so the interaction doesn't time out while connecting to RCON
    await interaction.response.defer(ephemeral=True)

    rcon_ip = os.getenv("RCON_IP")
    rcon_password = os.getenv("RCON_PASSWORD")
    rcon_port = int(os.getenv("RCON_PORT", 25575))

    if not rcon_ip or not rcon_password:
        await interaction.followup.send(
            "❌ Server config error: `RCON_IP` or `RCON_PASSWORD` is missing in environment variables."
        )
        return

    try:
        with MCRcon(rcon_ip, rcon_password, port=rcon_port) as mcr:
            response = mcr.command(f"whitelist add {username}")

            await interaction.followup.send(
                f"✅ Minecraft Server Response:\n> `{response}`"
            )

    except ConnectionRefusedError:
        await interaction.followup.send(
            "❌ Failed to connect to the Minecraft server. Is it running and is RCON enabled?"
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ An error occurred while executing the command: `{e}`"
        )


# Command to sync all commands on current server (for development)
@client.command()
async def sync(ctx):
    await client.tree.sync(guild=ctx.guild)
    await ctx.send(f"Synced to {ctx.guild.name}!")
