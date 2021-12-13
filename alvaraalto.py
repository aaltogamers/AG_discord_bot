#TODO#
#If text "!roll" roll from 1-100: couldn't fix#




#setup#
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot

import random
from random import choice

intents = discord.Intents.default()
intents.members = True
intents.reactions = True

client = commands.Bot(command_prefix = "!", intents = intents)

status = ["Vibing 8)", "😀", "😃", "😄", "😅", "🤣", "😇", "down bad😔", "tilted🤬", "Molding some glass", "Looking at your grades👀", "👨🏻‍🎓", "Gamin'", "League of Legends", "Rocket League", "CS:GO", "Hearthstone", "Browser games", "Civ 6", "With your feelings😈", "The Game"]

#automated roles globals#
reaction_title = ""
reactions = {}
reaction_message_id = ""

#tournament check-in globals#
#More can be added as needed#
tournament_name = "Standard tournament"
number_of_participants = 0
tournament_check = []
already_checked_in = 0

#queue globals#
queue_name = "Standard queue"
queue_members = []



@tasks.loop(seconds = 1800)
async def change_status():
    await client.change_presence(activity = discord.Game(choice(status)))

#events#

@client.event
async def on_ready():
    change_status.start()
    admin_channel = client.get_channel(805883542705799228)
    await admin_channel.send("Ines :D")

@client.event
async def on_member_join(member):
    guild = client.get_guild(273889488520871946)
    welcome_channel = guild.get_channel(805886391853514812)
    mbed = discord.Embed(title = "Welcome {}!".format(member.name), description = "Welcome to the Aalto gamers Discord server!\nHead over to the #roles channel to tell us what games you play and want roles for.\nAnd again, a warm welcome to you!", color = 0xFF4500)
    await welcome_channel.send(f"Welcome to the server {member.mention} 🥳")
    await member.send(embed = mbed)

@client.event
async def on_reaction_add(reaction, user):
    if not user.bot:
        message = reaction.message
        if str(message.id) == reaction_message_id:
            role_to_give = ""
            for role in reactions:
                if reactions[role] == reaction.emoji:
                    role_to_give = role
            role_for_reaction = discord.utils.get(user.guild.roles, name = role_to_give)
            await user.add_roles(role_for_reaction)

@client.event
async def on_reaction_remove(reaction, user):
    if not user.bot:
        message = reaction.message
        if str(message.id) == reaction_message_id:
            role_to_remove = ""
            for role in reactions:
                if reactions[role] == reaction.emoji:
                    role_to_remove = role
            role_for_reaction = discord.utils.get(user.guild.roles, name = role_to_remove)
            await user.remove_roles(role_for_reaction)

#commands#

@client.command(name = "ping", help = "Admin command")
async def ping(context):
    await context.send("Taasko kaatu puu ja veti sähköt? Ping: {:d}".format(round(client.latency * 1000)))

@client.command(name = "roll", help = "1-x random number generator. Remember to include anything after the !roll part (for example, !roll k). If x has words/non-numerals, default to 1-100.")
async def roll(context, numeroa):
    try:
        loppu = int(numeroa)
        await context.send(round(random.uniform(1, loppu)))
    except ValueError:
        await context.send(round(random.uniform(1, 100)))
    except TypeError:
        await context.send(round(random.uniform(1, 100)))
    except Exception:
        await context.send(round(random.uniform(1, 100)))

#automated role creation commands#

@client.command(name = "reaction_role_creation_commands", help = "Admin command")
async def reaction_role_creation_commands(context):
    mbed = discord.Embed(title = "Create Reaction Post", color = 0xFF4500)
    mbed.set_author(name = "Alvar Aalto")
    mbed.add_field(name = "Set Title", value = "!reaction_set_title \"New Title\"", inline = False)
    mbed.add_field(name = "Add Role", value = "!reaction_add_role @Role EMOJI_HERE", inline = False)
    mbed.add_field(name = "Remove Role", value = "!reaction_remove_role @Role", inline = False)
    mbed.add_field(name = "Send Creation Post", value = "!reaction_send_post", inline = False)
    await context.send(embed = mbed)
    await context.message.delete()

@client.command(name = "reaction_set_title", help = "Admin command")
async def reaction_set_title(context, new_title):
    global reaction_title
    reaction_title = new_title
    await context.send("The title is now `" + reaction_title + "`!")
    await context.message.delete()

@client.command(name = "reaction_add_role", help = "Admin command")
async def reaction_add_role(context, role: discord.Role, reaction):
    if role != None:
        reactions[role.name] = reaction
        await context.send("Role `" + role.name + "` has been added with the emblem " + reaction)
        await context.message.delete()
    else:
        await context.send("Something fucked up. You should probs add a role.")

@client.command(name = "reaction_remove_role", help = "Admin command")
async def reaction_remove_role(context, role: discord.Role):
    if role.name in reactions:
        del reactions[role.name]
        await context.send("Role `" + role.name + "` has been deleted")
        await context.message.delete()
    else:
        await context.send("Something fucked up. You never had that role.")
    
@client.command(name = "reaction_send_post", help = "Admin command")
async def reaction_send_post(context):

    description = "React to add the roles\n"
    for role in reactions:
        description += "`" + role + "` - " + reactions[role] + "\n"
    mbed = discord.Embed(title = reaction_title, description = description, color = 0xFF4500)
    mbed.set_author(name = "Alvar Aalto")
    message = await context.send(embed = mbed)
    global reaction_message_id
    reaction_message_id = str(message.id)
    for role in reactions:
        await message.add_reaction(reactions[role])
    await context.message.delete()

#tournament check-in commands#

@client.command(name = "tournament_creation_commands", help = "Admin command")
async def tournament_creation_commands(context):
    mbed = discord.Embed(title = "Create a tournament", color = 0xFF4500)
    mbed.set_author(name = "Alvar Aalto")
    mbed.add_field(name = "Give the tournament a name", value = "!set_tournament_name \"New Name\"", inline = False)
    mbed.add_field(name = "Give the amount of participants", value = "!set_participant_count x\n(NOTE: x is a whole number)", inline = False)
    await context.send(embed = mbed)
    await context.message.delete()

@client.command(name = "set_tournament_name", help = "Admin command")
async def set_tournament_name(context, new_name):
    global tournament_name
    tournament_name = new_name
    await context.send("The tournament name is now `" + tournament_name + "`")
    await context.message.delete()

@client.command(name = "set_participant_count", help = "Admin command")
async def set_participant_count(context, count):
    try:
        number = int(count)
        global number_of_participants
        number_of_participants = number
        await context.send("The tournament has `{:d}` participants".format(number_of_participants))
        await context.message.delete()
    except ValueError:
        await context.send("You fucked up. Put a whole number in.")

@client.command(name = "check_in", help = "Tournament check-in with the following format: !check_in \"Team name here\"")
async def check_in(context, team_name):
    team = str(team_name)
    global tournament_check
    tournament_check.append(team)
    global already_checked_in
    already_checked_in += 1
    global tournament_name
    mbed = discord.Embed(title = tournament_name + " check-in update", color = 0xFF4500)
    mbed.set_author(name = "Alvar Aalto")
    mbed.add_field(name = f"{context.author.name} has checked in " + team, value = "-----------------------", inline = False)
    team_string = ", ".join(tournament_check)
    global number_of_participants
    mbed.add_field(name = "So far `{:d}` out of `{:d}` teams have checked in: ".format(already_checked_in, number_of_participants), value = team_string, inline = False)
    mbed.add_field(name = "Reminder for the next team to check in:", value = "Put your team name in \"quotations\"", inline = False)
    await context.send(embed = mbed)

@client.command(name = "tournament_delete", help = "Admin command")
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


#queue commands#

@client.command(name = "queue_create", help = "Admin command")
async def queue_create(context, name):
    global queue_name
    queue_name = str(name)
    await context.send("The queue name is now `" + queue_name + "`")
    await context.message.delete()

@client.command(name = "queue_start", help = "Admin command")
async def queue_start(context):
    global queue_name
    mbed = discord.Embed(title = queue_name, color = 0xFF4500)
    mbed.set_author(name = "Alvar Aalto")
    mbed.add_field(name = "The queue has been started", value = "No players in queue...\nso far ;)", inline = False)
    await context.send(embed = mbed)

@client.command(name = "queue_up", help = "Join the current queue")
async def queue_up(context):
    global queue_members
    global queue_name
    gamer = str(context.author.name)
    queue_members.append(gamer)
    many = len(queue_members)
    queue_string = "\n".join(queue_members)
    mbed = discord.Embed(title = queue_name, color = 0xFF4500)
    mbed.set_author(name = "Alvar Aalto")
    mbed.add_field(name = f"{context.author.name} has joined the queue!", value = "{:d} people in queue so far".format(many), inline = False)
    mbed.add_field(name = "People in order of joining:", value = queue_string, inline = False)
    await context.send(embed = mbed)

@client.command(name = "queue_delete", help = "Admin command")
async def queue_delete(context):
    global queue_members
    global queue_name
    queue_name = ""
    queue_members = []
    await context.send("The current queue has been deleted")
    await context.message.delete()



#run#
client.run("Nzk4MjI3OTU5MzEwOTc1MDU3.X_x9tw.BZWYsveH5cOtOuT-QypzC1-89i4")
