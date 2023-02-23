import discord
from discord import app_commands
from .setup import client
import itertools

queues = {}


class LobbyGroup:
    def __init__(self, lobbies):
        lobbies.sort(key=lambda lobby: lobby.game)
        self.lobbies = lobbies

    def memberCount(self):
        count = 0
        for lobby in self.lobbies:
            count += lobby.memberCount
        return count

    def games(self):
        return list(map(lambda lobby: lobby.game, self.lobbies))

    def gamesString(self):
        return "_".join(self.games())

    def __str__(self):
        return f"{self.memberCount()}{list(map(lambda lobby: lobby.__str__(), self.lobbies))}"

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, LobbyGroup):
            return self.lobbies == __o.lobbies
        return False


class Lobby:
    def __init__(self, game, members):
        self.game = game
        self.members = members
        self.memberCount = len(members)

    def __str__(self):
        return f"{self.game}: {self.members}"

    def __eq__(self, __o: object) -> bool:

        if isinstance(__o, Lobby):
            return self.game == __o.game and set(self.members) == set(__o.members)
        return False


class Queue:
    def __init__(self, name, itemDict, messageId):
        self.name = name
        self.members = {}
        self.possibilities = []
        self.itemDict = itemDict
        self.messageId = messageId

    def add_member(self, member):
        self.members[member.id] = member

    def remove_member(self, id):
        self.members.pop(id)

    def updatePossibilities(self):
        possibilities = []
        allPossibleLobbies = []
        for itemName, itemPlayerCount in self.itemDict.items():
            possibleMembers = list(
                map(
                    lambda member: member.id,
                    filter(
                        lambda member: itemName in member.items, self.members.values()
                    ),
                )
            )

            possibleCombinationsForGame = itertools.combinations(
                possibleMembers, itemPlayerCount
            )
            for comb in possibleCombinationsForGame:
                lobby = Lobby(itemName, comb)
                allPossibleLobbies.append(lobby)

        def removeUnviableAndMakeGroup(lobby, lobbyGroup, remainingLobbies):
            lobbies = lobbyGroup.lobbies.copy()
            lobbies.append(lobby)
            lobbyGroup = LobbyGroup(lobbies)
            filteredLobbies = list(
                filter(
                    lambda otherLobby: set(lobby.members).isdisjoint(
                        otherLobby.members
                    ),
                    remainingLobbies,
                )
            )
            if filteredLobbies.__len__() == 0:
                possibilities.append(lobbyGroup)
                return
            else:
                for subLobby in filteredLobbies:
                    removeUnviableAndMakeGroup(subLobby, lobbyGroup, filteredLobbies)

        lobbyGroup = LobbyGroup([])
        for lobby in allPossibleLobbies:
            removeUnviableAndMakeGroup(lobby, lobbyGroup, allPossibleLobbies)

        possibilities.sort(
            key=lambda lobbyGroup: lobbyGroup.memberCount(), reverse=True
        )
        uniquePossibilities = []
        for possibility in possibilities:
            if possibility not in uniquePossibilities:
                uniquePossibilities.append(possibility)

        possibilitiesGroupedByGame = {}
        for possibility in uniquePossibilities:
            games = possibility.gamesString()
            if games not in possibilitiesGroupedByGame:
                possibilitiesGroupedByGame[games] = []
            possibilitiesGroupedByGame[games].append(possibility)

        print(possibilities.__len__())
        print(uniquePossibilities.__len__())

        for _, possibilitiesForSpesificGameGroup in possibilitiesGroupedByGame.items():
            print(possibilitiesForSpesificGameGroup[0])

    def __str__(self):
        separator = ", "
        itemsAsStrings = []
        membersAsStrings = []
        for value in self.itemDict.items():
            itemsAsStrings.append(value.__str__())
        for value in self.members.values():
            membersAsStrings.append(value.__str__())
        return f"{self.name}. Options: [{separator.join(itemsAsStrings)}].\nMembers: [{separator.join(membersAsStrings)}]"


class QueueMember:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.items = []

    def update_items(self, items):
        self.items = items

    def remove_item(self, index):
        self.items.pop(index)

    def __str__(self):
        separator = ", "
        return f"{self.name}: [{separator.join(self.items)}]"


testMembers = []

testGames = [
    ["LoL"],
    ["LoL", "CSGO"],
    ["LoL", "CSGO", "Valorant"],
    ["LoL", "CSGO", "Overwatch"],
    ["Lol", "CSGO", "Valorant", "Overwatch"],
    ["Lol", "CSGO", "Valorant", "Overwatch"],
    ["LoL", "CSGO"],
    ["LoL", "CSGO"],
    ["LoL", "CSGO"],
    ["Lol"],
    ["Lol"],
    ["CSGO"],
    ["CSGO"],
    ["CSGO"],
    ["CSGO"],
    ["Valorant"],
    ["Valorant"],
    ["Valorant"],
    ["Overwatch"],
    ["Overwatch"],
    ["Overwatch"],
    ["Overwatch"],
    ["Overwatch"],
]

for i in range(0, testGames.__len__() - 1):
    testMember = QueueMember(f"Test{i}", i)
    items = testGames[i]
    testMember.update_items(items)
    testMembers.append(testMember)


class Select(discord.ui.Select):
    def __init__(self, queue: Queue):
        self.queueName = queue.name
        optionElems = []
        for key, _ in queue.itemDict.items():
            optionElems.append(discord.SelectOption(label=key))
        super().__init__(
            placeholder=f"Choose what you want to play",
            max_values=queue.itemDict.__len__(),
            min_values=0,
            options=optionElems,
        )

    async def callback(self, interaction: discord.Interaction):
        queue = queues[self.queueName]
        user = interaction.user
        if user.id not in queue.members:
            queue.add_member(QueueMember(user.name, user.id))
        queueMember = queue.members[user.id]
        queueMember.update_items(self.values)
        channel = interaction.channel
        message = await channel.fetch_message(queue.messageId)
        embed = message.embeds[0]
        embed.description = queue.__str__()
        await message.edit(embed=embed)
        await interaction.response.defer()


class SelectView(discord.ui.View):
    def __init__(self, queue: Queue):
        super().__init__()
        self.add_item(Select(queue))


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
    for member in testMembers:
        queue.add_member(member)
    queue.updatePossibilities()
    queues[name] = queue
    await interaction.response.send_message(
        content=f"Select what you want to play in {name}:",
        view=SelectView(queue),
    )


queue = Queue("Cool", {"LoL": 10, "CSGO": 10, "Overwatch": 6, "Valorant": 5}, 1)
for member in testMembers:
    queue.add_member(member)
queue.updatePossibilities()
