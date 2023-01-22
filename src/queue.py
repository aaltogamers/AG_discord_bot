import discord
from .setup import client

# queue globals#
queue_name = "Standard queue"
queue_members = []


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
