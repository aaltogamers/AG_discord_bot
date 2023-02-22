import discord
from discord import app_commands
from .setup import client

queues = {}


class Queue:
    def __init__(self, name, items, messageId):
        self.name = name
        self.members = {}
        self.items = items
        self.messageId = messageId

    def add_member(self, member):
        self.members[member.id] = member

    def remove_member(self, id):
        self.members.pop(id)

    def __str__(self):
        separator = ", "
        itemsAsStrings = []
        membersAsStrings = []
        for value in self.items.items():
            itemsAsStrings.append(value.__str__())
        for value in self.members.values():
            membersAsStrings.append(value.__str__())
        return f"{self.name}. Options: [{separator.join(itemsAsStrings)}].\nMembers: [{separator.join(membersAsStrings)}]"


class QueueMember:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.items = {}

    def add_item(self, item, index):
        self.items[index] = item

    def remove_item(self, index):
        self.items.pop(index)

    def __str__(self):
        separator = ", "
        itemsAsStrings = []
        for value in self.items.items():
            itemsAsStrings.append(value.__str__())
        return f"{self.name}: [{separator.join(itemsAsStrings)}]"


class Select(discord.ui.Select):
    def __init__(self, index, queue: Queue):
        self.index = index
        self.queueName = queue.name
        optionElems = []
        for key, _ in queue.items.items():
            optionElems.append(discord.SelectOption(label=key))
        super().__init__(
            placeholder=f"{index}. Preference",
            max_values=1,
            min_values=0,
            options=optionElems,
        )

    async def callback(self, interaction: discord.Interaction):
        queue = queues[self.queueName]
        user = interaction.user
        if user.id not in queue.members:
            queue.add_member(QueueMember(user.name, user.id))
        queueMember = queue.members[user.id]
        if self.values.__len__() != 0:
            selectedItem = self.values[0]
            queueMember.add_item(selectedItem, self.index)
        else:
            queueMember.remove_item(self.index)
        channel = interaction.channel
        message = await channel.fetch_message(queue.messageId)
        embed = message.embeds[0]
        embed.description = queue.__str__()
        await message.edit(embed=embed)
        await interaction.response.defer()


class SelectView(discord.ui.View):
    def __init__(self, queue: Queue):
        super().__init__()
        for i, _ in enumerate(queue.items):
            self.add_item(Select(i + 1, queue))


@client.tree.command(description="Start a new queue. Ex. /queue Biweekly Lol:5,CSGO:10")
@app_commands.describe(
    name="name of the queue", items="items for queue. Format item:amount, ex. LoL:5"
)
async def queue(interaction: discord.Interaction, name: str, items: str):
    title = f"{name} queue"
    embed = discord.Embed(title=title, color=0xFF4500)
    itemsDict = {}
    for item in items.split(","):
        key, value = item.split(":")
        itemsDict[key] = int(value)
    res = await interaction.channel.send(embed=embed)
    queue = Queue(name, itemsDict, res.id)
    queues[name] = queue
    await interaction.response.send_message(
        content="Select your prefferences in order:",
        view=SelectView(queue),
    )
