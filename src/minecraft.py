import discord
from .setup import client
from mcipc.query import Client


@client.tree.command(
    name="mc_server_status",
    description="Lists info about the Minecraft server's players",
)
async def mc(interaction: discord.Interaction):
    # Use minecraft server as client and get list of players currently in-game
    with Client("minecraft.aaltogamers.fi", 25565) as cli:
        msg = f"**Minecraft server stats:**\n"
        stats = cli.stats(True)
        msg += f"Number of players: **{stats.num_players}**/{stats.max_players}\n"
        msg += "Currently playing: `" + str(stats.players) + "`"
        await interaction.response.send_message(msg)
