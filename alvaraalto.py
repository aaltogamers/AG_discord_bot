from mcipc.query import Client
from random import choice
import random
import discord
from discord.ext import commands, tasks
from discord import app_commands
import re
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

# tournament check-in globals#
# More can be added as needed#
tournament_name = "Standard tournament"
number_of_participants = 0
tournament_check = []
already_checked_in = 0

# queue globals#
queue_name = "Standard queue"
queue_members = []


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


# Events


@client.event
async def on_ready():
    change_status.start()
    client.tree.copy_global_to(guild=getGuild())
    await client.tree.sync()


@client.event
async def on_member_join(member):
    guild = getGuild()
    welcome_channel = guild.get_channel(805886391853514812)
    mbed = discord.Embed(
        title="Welcome {}!".format(member.name),
        description="Welcome to the Aalto gamers Discord server!\nHead over to the #roles channel to tell us what games you play and want roles for.\nAnd again, a warm welcome to you!",
        color=0xFF4500,
    )
    await welcome_channel.send(f"Welcome to the server {member.mention} 🥳")
    await member.send(embed=mbed)


@client.event
async def on_raw_reaction_add(rawReaction):
    try:
        if rawReaction.message_id == roleMessageId:
            role = await getRoleFromEmoji(rawReaction.emoji)
            await addRole(role, rawReaction.member)
    except Exception as e:
        await traceErrorAndSendErrorMessage()


@client.event
async def on_raw_reaction_remove(rawReaction):
    try:
        if rawReaction.message_id == roleMessageId:
            role = await getRoleFromEmoji(rawReaction.emoji)
            guild = getGuild()
            user = guild.get_member(rawReaction.user_id)
            await removeRole(role, user)
    except Exception as e:
        await traceErrorAndSendErrorMessage()


# Commands


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


async def sendErrorMessage(message):
    channel = client.get_channel(errorMessageChannnelId)
    await channel.send(message)


async def traceErrorAndSendErrorMessage():
    await sendErrorMessage(traceback.format_exc())


# Role creation commands


async def getValidRoles():
    guild = getGuild()
    allRoles = await guild.fetch_roles()
    validRoles = list(
        filter(
            lambda role: not (
                role.permissions.manage_roles
                or role.permissions.administrator
                or role.name == "@everyone"
            ),
            allRoles,
        )
    )
    return validRoles


async def getRolesAndEmojis():
    channel = client.get_channel(roleChannelId)
    message = await channel.fetch_message(roleMessageId)
    textAndEmojis = re.findall(r".+ - .", message.content)
    rolesAndEmojis = {}
    for textAndEmoji in textAndEmojis:
        text, emoji = textAndEmoji.split(" - ")
        rolesAndEmojis[emoji] = text
    return rolesAndEmojis


async def getRoleFromEmoji(emoji):
    rolesAndEmojis = await getRolesAndEmojis()
    emoji = emoji
    return rolesAndEmojis[emoji.name]


async def addRole(role, user):
    roles = await getValidRoles()
    roleToAdd = discord.utils.get(roles, name=role)
    roleExists = roleToAdd != None
    alreadyHasRole = roleToAdd in user.roles
    if roleExists and alreadyHasRole:
        return f"You already have the role *{roleToAdd.name}*"
    elif roleExists:
        await user.add_roles(roleToAdd)
        return f"Added role *{roleToAdd.name}*"
    else:
        raise Exception(f"Invalid role *{role}*")


async def removeRole(role, user):
    roles = await getValidRoles()
    roleToRemove = discord.utils.get(roles, name=role)
    roleExists = roleToRemove != None
    alreadyHasRole = roleToRemove in user.roles
    if roleExists and alreadyHasRole:
        await user.remove_roles(roleToRemove)
        return f"Removed role *{roleToRemove.name}*"
    elif roleExists:
        return f"You don't have the role *{roleToRemove.name}*"
    else:
        raise Exception(f"Invalid role *{role}*")


@client.tree.command(description="Add a role to yourself.")
@app_commands.describe(role="The name of the role you want to add.")
async def add_role(interaction: discord.Interaction, role: str):
    user: discord.User = interaction.user
    await interaction.response.send_message(await addRole(role, user))


@client.tree.command(description="Remove a role from yourself.")
@app_commands.describe(role="The name of the role you want to remove.")
async def remove_role(interaction: discord.Interaction, role: str):
    user: discord.User = interaction.user
    await interaction.response.send_message(await removeRole(role, user))


@client.tree.command(description="List all roles you can add/remove.")
@app_commands.describe()
async def list_roles(interaction: discord.InteractionMessage):
    validRoles = await getValidRoles()
    roleNamesList = list(map(lambda role: role.name, validRoles))
    roleNames = ", ".join(roleNamesList)
    await interaction.response.send_message(
        f"Roles that can be added/removed: {roleNames}"
    )


# Tournament check-in commands#


@client.command(name="tournament_creation_commands", help="Admin command")
async def tournament_creation_commands(context):
    mbed = discord.Embed(title="Create a tournament", color=0xFF4500)
    mbed.set_author(name="Alvar Aalto")
    mbed.add_field(
        name="Give the tournament a name",
        value='!set_tournament_name "New Name"',
        inline=False,
    )
    mbed.add_field(
        name="Give the amount of participants",
        value="!set_participant_count x\n(NOTE: x is a whole number)",
        inline=False,
    )
    await context.send(embed=mbed)
    await context.message.delete()


@client.command(name="set_tournament_name", help="Admin command")
async def set_tournament_name(context, new_name):
    global tournament_name
    tournament_name = new_name
    await context.send("The tournament name is now `" + tournament_name + "`")
    await context.message.delete()


@client.command(name="set_participant_count", help="Admin command")
async def set_participant_count(context, count):
    try:
        number = int(count)
        global number_of_participants
        number_of_participants = number
        await context.send(
            "The tournament has `{:d}` participants".format(number_of_participants)
        )
        await context.message.delete()
    except ValueError:
        await context.send("You fucked up. Put a whole number in.")


@client.command(
    name="check_in",
    help='Tournament check-in with the following format: !check_in "Team name here"',
)
async def check_in(context, team_name):
    team = str(team_name)
    global tournament_check
    tournament_check.append(team)
    global already_checked_in
    already_checked_in += 1
    global tournament_name
    mbed = discord.Embed(title=tournament_name + " check-in update", color=0xFF4500)
    mbed.set_author(name="Alvar Aalto")
    mbed.add_field(
        name=f"{context.author.name} has checked in " + team,
        value="-----------------------",
        inline=False,
    )
    team_string = ", ".join(tournament_check)
    global number_of_participants
    mbed.add_field(
        name="So far `{:d}` out of `{:d}` teams have checked in: ".format(
            already_checked_in, number_of_participants
        ),
        value=team_string,
        inline=False,
    )
    mbed.add_field(
        name="Reminder for the next team to check in:",
        value='Put your team name in "quotations"',
        inline=False,
    )
    await context.send(embed=mbed)


@client.command(name="tournament_delete", help="Admin command")
async def tournament_delete(context):
    global tournament_name
    tournament_name = ""
    global number_of_participants
    number_of_participants = 0
    global tournament_check
    tournament_check = []
    global already_checked_in
    already_checked_in = 0
    await context.send("The current tournament has been deleted")
    await context.message.delete()


# Queue commands#


@client.command(name="queue_create", help="Admin command")
async def queue_create(context, name):
    global queue_name
    queue_name = str(name)
    await context.send("The queue name is now `" + queue_name + "`")
    await context.message.delete()


@client.command(name="queue_start", help="Admin command")
async def queue_start(context):
    global queue_name
    mbed = discord.Embed(title=queue_name, color=0xFF4500)
    mbed.set_author(name="Alvar Aalto")
    mbed.add_field(
        name="The queue has been started",
        value="No players in queue...\nso far ;)",
        inline=False,
    )
    await context.send(embed=mbed)


@client.command(name="queue_up", help="Join the current queue")
async def queue_up(context):
    global queue_members
    global queue_name
    gamer = str(context.author.name)
    queue_members.append(gamer)
    many = len(queue_members)
    queue_string = "\n".join(queue_members)
    mbed = discord.Embed(title=queue_name, color=0xFF4500)
    mbed.set_author(name="Alvar Aalto")
    mbed.add_field(
        name=f"{context.author.name} has joined the queue!",
        value="{:d} people in queue so far".format(many),
        inline=False,
    )
    mbed.add_field(name="People in order of joining:", value=queue_string, inline=False)
    await context.send(embed=mbed)


@client.command(name="queue_delete", help="Admin command")
async def queue_delete(context):
    global queue_members
    global queue_name
    queue_name = ""
    queue_members = []
    await context.send("The current queue has been deleted")
    await context.message.delete()


# Minecraft server stuff


# A command to get the players in the server


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


# run#

client.run(client_secret)
