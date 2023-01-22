import discord
from .setup import client

tournament_name = "Standard tournament"
number_of_participants = 0
tournament_check = []
already_checked_in = 0


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
