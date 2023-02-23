from __future__ import annotations
import discord
from discord import app_commands
from .setup import client
import itertools
import typing


queues = {}


def allToString(list: typing.Iterable[typing.Any]) -> list[str]:
    asStrings: list[str] = []
    for item in list:
        asStrings.append(str(item))
    return asStrings


class Lobby:
    def __init__(self, game: str, memberIds: list[int]):
        self.game = game
        self.memberIds = memberIds
        self.memberCount = len(memberIds)

    def __str__(self):
        return f"{self.game}: {self.memberIds}"

    def prettyString(self, queue: Queue):
        joinString = ", "
        memberUsernames: list[str] = []
        for memberId in self.memberIds:
            memberUsernames.append(queue.members[memberId].name)
        return f"{self.game}: ({joinString.join(memberUsernames)})"

    def __eq__(self, __o: object) -> bool:

        if isinstance(__o, Lobby):
            return self.game == __o.game and set(self.memberIds) == set(__o.memberIds)
        return False


class LobbyGroup:
    def __init__(self, lobbies: list[Lobby]):
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
        return ", ".join(self.games())

    def __str__(self):
        return f"{self.memberCount()}:{allToString(self.lobbies)}"

    def prettyString(self, queue: Queue):
        joinString = "\n"
        lobbiesString = joinString.join(
            map(lambda lobby: lobby.prettyString(queue), self.lobbies)
        )
        return f"{self.memberCount()} players: Ex.\n{lobbiesString}"

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, LobbyGroup):
            return self.lobbies == __o.lobbies
        return False


def isSublist(s: list[str], l: list[str]):
    len_s = len(s)  # so we don't recompute length of s on every iteration
    return any(s == l[i : len_s + i] for i in range(len(l) - len_s + 1))


class Queue:
    def __init__(self, name: str, itemDict: dict[str, int], messageId: int):
        self.name = name
        self.members: dict[int, QueueMember] = {}
        self.possibilities = []
        self.itemDict = itemDict
        self.messageId = messageId

    def add_member(self, member: QueueMember):
        self.members[member.id] = member

    def remove_member(self, id: int):
        self.members.pop(id)

    def updatePossibilities(self) -> tuple[int, list[LobbyGroup]]:
        possibilities: list[LobbyGroup] = []
        allPossibleLobbies: list[Lobby] = []
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
            comb: list[int]
            for comb in possibleCombinationsForGame:  # type: ignore
                lobby = Lobby(itemName, comb)
                allPossibleLobbies.append(lobby)

        def removeUnviableAndMakeGroup(
            lobby: Lobby, lobbyGroup: LobbyGroup, remainingLobbies: list[Lobby]
        ):
            lobbies = lobbyGroup.lobbies.copy()
            lobbies.append(lobby)
            lobbyGroup = LobbyGroup(lobbies)
            filteredLobbies = list(
                filter(
                    lambda otherLobby: set(lobby.memberIds).isdisjoint(
                        otherLobby.memberIds
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
        uniquePossibilities: list[LobbyGroup] = []
        for possibility in possibilities:
            if possibility not in uniquePossibilities:
                uniquePossibilities.append(possibility)

        possibilitiesGroupedByGame: dict[str, list[LobbyGroup]] = {}
        for possibility in uniquePossibilities:
            games = possibility.gamesString()
            if games not in possibilitiesGroupedByGame:
                possibilitiesGroupedByGame[games] = []
            possibilitiesGroupedByGame[games].append(possibility)

        onePossibilityPerGameGroup: list[LobbyGroup] = []
        for _, possibilitiesForSpesificGameGroup in possibilitiesGroupedByGame.items():
            onePossibilityPerGameGroup.append(possibilitiesForSpesificGameGroup[0])

        onePossibilityPerGameGroupMinusRedundant: list[LobbyGroup] = []
        for possibility in onePossibilityPerGameGroup:
            isSubOfAnother = any(
                map(
                    lambda otherPossibility: possibility.gamesString()
                    != otherPossibility.gamesString()
                    and isSublist(possibility.games(), otherPossibility.games()),
                    onePossibilityPerGameGroup,
                )
            )
            if not isSubOfAnother:
                onePossibilityPerGameGroupMinusRedundant.append(possibility)

        return (uniquePossibilities.__len__(), onePossibilityPerGameGroupMinusRedundant)

    def __str__(self):
        separator = ", "
        itemsAsStrings: list[str] = allToString(self.itemDict.items())
        membersAsStrings: list[str] = allToString(self.members.values())
        return f"{self.name}. Options: [{separator.join(itemsAsStrings)}].\nMembers: [{separator.join(membersAsStrings)}]"


class QueueMember:
    def __init__(self, name: str, id: int, joinIndex: int):
        self.name = name
        self.id = id
        self.joinIndex = joinIndex
        self.items = []

    def update_items(self, items: list[str]):
        self.items = items

    def remove_item(self, index: int):
        self.items.pop(index)

    def __str__(self):
        separator = ", "
        return f"{self.name}: [{separator.join(self.items)}]"


class Select(discord.ui.Select):  # type: ignore
    def __init__(self, queue: Queue):
        self.queueName = queue.name
        optionElems: list[discord.SelectOption] = []
        for key, _ in queue.itemDict.items():
            optionElems.append(discord.SelectOption(label=key))
        super().__init__(
            placeholder=f"Choose what you want to play",
            max_values=queue.itemDict.__len__(),
            min_values=0,
            options=optionElems,
        )

    async def callback(self, interaction: discord.Interaction):
        queue: Queue = queues[self.queueName]
        user = interaction.user
        if user.id not in queue.members:
            queue.add_member(QueueMember(user.name, user.id, queue.members.__len__()))
        queueMember = queue.members[user.id]
        queueMember.update_items(self.values)
        channel: discord.TextChannel = interaction.channel  # type: ignore
        message: discord.Message = await channel.fetch_message(queue.messageId)
        oldEmbed = message.embeds[0]
        embed = discord.Embed(title=oldEmbed.title, color=0xFF4500)
        (possibleLobbyCount, possibleLobbies) = queue.updatePossibilities()
        embed.add_field(
            name="Total possible lobbies", value=possibleLobbyCount, inline=False
        )
        for lobbyGroup in possibleLobbies:
            embed.add_field(
                name=lobbyGroup.gamesString(),
                value=lobbyGroup.prettyString(queue),
                inline=False,
            )

        queue.updatePossibilities()
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
    res = await interaction.channel.send(embed=embed)  # type: ignore
    queue = Queue(name, itemsDict, res.id)  # type: ignore
    for member in testMembers:
        queue.add_member(member)
    queue.updatePossibilities()
    queues[name] = queue
    await interaction.response.send_message(
        content=f"Select what you want to play in {name}:",
        view=SelectView(queue),
    )


testMembers: list[QueueMember] = []

testGames = [
    ["LoL"],
    ["LoL", "CSGO"],
    ["LoL", "CSGO", "Valorant"],
    ["LoL", "CSGO", "Overwatch"],
    ["LoL", "CSGO", "Valorant", "Overwatch"],
    ["LoL", "CSGO", "Valorant", "Overwatch"],
    ["LoL", "CSGO"],
    ["LoL", "CSGO"],
    ["LoL", "CSGO"],
    ["LoL"],
    ["LoL"],
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
    testMember = QueueMember(f"Gamer{i}", i, i)
    items = testGames[i]
    testMember.update_items(items)
    testMembers.append(testMember)


queue: Queue = Queue("Cool", {"LoL": 10, "CSGO": 10, "Overwatch": 6, "Valorant": 5}, 1)  # type: ignore
for member in testMembers:
    queue.add_member(member)
queue.updatePossibilities()
