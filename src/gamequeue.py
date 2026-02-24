from __future__ import annotations
import discord
from discord import app_commands
from .setup import client
import itertools
from collections import Counter

queues: dict[str, Queue] = {}


class Lobby:
    def __init__(self, game: str, memberIds: list[int]):
        self.game = game
        self.memberIds = memberIds
        self.memberCount = len(memberIds)

    def __str__(self):
        return f"{self.game}: {self.memberIds}"

    def prettyString(self, queue: Queue):
        memberUsernames = [queue.members[m_id].name for m_id in self.memberIds]
        return f"{self.game}: ({', '.join(memberUsernames)})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Lobby):
            return self.game == other.game and set(self.memberIds) == set(
                other.memberIds
            )
        return False


class LobbyGroup:
    def __init__(self, lobbies: list[Lobby]):
        # Sort lobbies to ensure consistent ordering
        self.lobbies = sorted(lobbies, key=lambda lobby: lobby.game)

    def memberCount(self):
        return sum(lobby.memberCount for lobby in self.lobbies)

    def games(self):
        return [lobby.game for lobby in self.lobbies]

    def gamesString(self):
        return ", ".join(self.games())

    def __str__(self):
        return f"{self.memberCount()}: {[str(l) for l in self.lobbies]}"

    def prettyString(self, queue: Queue):
        lobbiesString = "\n".join(lobby.prettyString(queue) for lobby in self.lobbies)
        return f"{self.memberCount()} players: Ex.\n{lobbiesString}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, LobbyGroup):
            return self.lobbies == other.lobbies
        return False


class QueueMember:
    def __init__(self, name: str, member_id: int, joinIndex: int):
        self.name = name
        self.id = member_id
        self.joinIndex = joinIndex
        self.items: list[str] = []

    def update_items(self, items: list[str]):
        self.items = items

    def __str__(self):
        return f"{self.name}: [{', '.join(self.items)}]"


class Queue:
    def __init__(self, name: str, itemDict: dict[str, int]):
        self.name = name
        self.members: dict[int, QueueMember] = {}
        self.itemDict = itemDict
        self.messageId: int | None = None

    def add_member(self, member: QueueMember):
        self.members[member.id] = member

    def remove_member(self, member_id: int):
        self.members.pop(member_id, None)

    def updatePossibilities(self) -> tuple[int, tuple[int, list[LobbyGroup]]]:
        if not self.members:
            return 0, (0, [])

        max_size = max(self.itemDict.values(), default=1)
        for playerCountMinus in range(max_size):
            possibilities = self.getPossibilities(playerCountMinus)
            if possibilities[1]:  # If we found valid lobby groups
                return playerCountMinus, possibilities

        return max_size - 1, (0, [])

    def getPossibilities(self, playerCountMinus: int) -> tuple[int, list[LobbyGroup]]:
        allPossibleLobbies: list[Lobby] = []

        # 1. Generate all valid single lobbies
        for itemName, itemPlayerCount in self.itemDict.items():
            required_players = max(itemPlayerCount - playerCountMinus, 1)
            possibleMembers = [
                m.id for m in self.members.values() if itemName in m.items
            ]

            for comb in itertools.combinations(possibleMembers, required_players):
                allPossibleLobbies.append(Lobby(itemName, list(comb)))

        # Sort for deterministic backtracking
        allPossibleLobbies.sort(key=lambda l: (l.game, tuple(l.memberIds)))

        possibilities: list[LobbyGroup] = []

        # 2. Backtracking to find disjoint lobby sets
        def backtrack(
            start_idx: int, current_group: list[Lobby], current_members: set[int]
        ):
            is_maximal = True
            for i in range(start_idx, len(allPossibleLobbies)):
                lobby = allPossibleLobbies[i]
                lobby_members = set(lobby.memberIds)

                if current_members.isdisjoint(lobby_members):
                    is_maximal = False
                    current_group.append(lobby)
                    backtrack(
                        i + 1, current_group, current_members.union(lobby_members)
                    )
                    current_group.pop()

            if is_maximal and current_group:
                possibilities.append(LobbyGroup(current_group.copy()))

        backtrack(0, [], set())

        # 3. Filter down to unique possibilities
        unique_possibilities: list[LobbyGroup] = []
        seen = set()
        for p in possibilities:
            ident = tuple(sorted(str(l) for l in p.lobbies))
            if ident not in seen:
                seen.add(ident)
                unique_possibilities.append(p)

        # 4. Group by game configuration and remove subsets
        unique_possibilities.sort(key=lambda lg: lg.memberCount(), reverse=True)
        best_per_game_combo: dict[tuple[str, ...], LobbyGroup] = {}

        for p in unique_possibilities:
            games_tuple = tuple(sorted(p.games()))
            if games_tuple not in best_per_game_combo:
                best_per_game_combo[games_tuple] = p

        final_possibilities: list[LobbyGroup] = []
        for games_tuple, poss in best_per_game_combo.items():
            is_sub = False
            for other_games_tuple in best_per_game_combo.keys():
                if games_tuple == other_games_tuple:
                    continue
                # Multiset subset check
                c_sub, c_main = Counter(games_tuple), Counter(other_games_tuple)
                if all(c_main[k] >= v for k, v in c_sub.items()):
                    is_sub = True
                    break
            if not is_sub:
                final_possibilities.append(poss)

        return len(unique_possibilities), final_possibilities

    def __str__(self):
        itemsAsStrings = [f"{k}:{v}" for k, v in self.itemDict.items()]
        membersAsStrings = [str(m) for m in self.members.values()]
        return f"{self.name}. Options: [{', '.join(itemsAsStrings)}].\nMembers: [{', '.join(membersAsStrings)}]"


class Select(discord.ui.Select):
    def __init__(self, queue: Queue):
        self.queueName = queue.name
        optionElems = [discord.SelectOption(label=key) for key in queue.itemDict.keys()]

        # Discord limits select max_values to max 25.
        safe_max_values = min(len(optionElems), 25)

        super().__init__(
            placeholder="Choose what you want to play",
            max_values=safe_max_values,
            min_values=0,
            options=optionElems,
        )

    async def callback(self, interaction: discord.Interaction):
        # 🐛 Defer FIRST to prevent 'Interaction Failed' timeout errors during heavy calculation
        await interaction.response.defer()

        queue = queues.get(self.queueName)
        if not queue:
            return  # Guard in case the queue is missing in memory

        user = interaction.user
        if user.id not in queue.members:
            queue.add_member(QueueMember(user.name, user.id, len(queue.members)))

        queueMember = queue.members[user.id]
        queueMember.update_items(self.values)

        if queue.messageId:
            channel: discord.TextChannel = interaction.channel  # type: ignore
            message: discord.Message = await channel.fetch_message(queue.messageId)

            oldEmbed = message.embeds[0]
            embed = discord.Embed(title=oldEmbed.title, color=0xFF4500)

            # Condense games into a single field to protect against Discord's 25-field limit
            totalGames = [
                game for member in queue.members.values() for game in member.items
            ]
            game_counts = "\n".join(
                f"*{game}*: {totalGames.count(game)}" for game in queue.itemDict.keys()
            )
            embed.add_field(
                name="__Players per game__", value=game_counts or "None", inline=False
            )

            missingPlayerAmount, (possibleLobbyCount, possibleLobbies) = (
                queue.updatePossibilities()
            )

            embed.add_field(
                name="__Total possible lobbies__",
                value=str(possibleLobbyCount),
                inline=False,
            )

            if missingPlayerAmount > 0:
                embed.add_field(
                    name="__Missing players__",
                    value=f"These lobbies are {missingPlayerAmount} players short",
                    inline=False,
                )

            embed.add_field(name="__Lobbies__", value="", inline=False)

            # Limit the displayed lobbies to prevent field limit crashes
            for lobbyGroup in possibleLobbies[:15]:
                embed.add_field(
                    name=f"*{lobbyGroup.gamesString()}*",
                    value=lobbyGroup.prettyString(queue),
                    inline=False,
                )

            if len(possibleLobbies) > 15:
                embed.add_field(
                    name="...",
                    value=f"*(And {len(possibleLobbies) - 15} more combinations)*",
                    inline=False,
                )

            await message.edit(embed=embed)


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
        itemsDict[key.strip()] = int(value.strip())

    queue_obj = Queue(name, itemsDict)
    queues[name] = queue_obj

    await interaction.response.send_message(
        content=f"Select what you want to play in {name}:",
        view=SelectView(queue_obj),
    )

    messageRes = await interaction.channel.send(embed=embed)  # type: ignore
    queue_obj.messageId = messageRes.id
