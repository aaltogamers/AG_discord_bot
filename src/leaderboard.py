import requests
import base64
import yaml
import json
from .setup import GITHUB_TOKEN, client, getGuild, IS_DEV_MODE
import discord
from discord import app_commands
import datetime


def getFileContentAndSha():
    fileInfoResponse = requests.get(
        url="https://api.github.com/repos/aaltogamers/AG_web/contents/src/content/leaderboard.md"
    )
    sha = fileInfoResponse.json()["sha"]
    fileContentBase64 = fileInfoResponse.json()["content"]
    fileContentString = (
        base64.b64decode(fileContentBase64).decode("utf-8").strip()[3:-3]
    )
    fileContent = yaml.load(fileContentString, Loader=yaml.FullLoader)
    return fileContent, sha


def commitFileContent(fileContent, sha):
    yamlString = yaml.dump(fileContent)
    yamlString = "---\n" + yamlString + "---"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = {
        "message": "Updated leaderboard using Discord bot",
        "committer": {"name": "AG Board", "email": "board@aaltogamers.fi"},
        "content": base64.b64encode(yamlString.encode("utf-8")).decode("utf-8"),
        "sha": sha,
    }
    response = requests.put(
        url="https://api.github.com/repos/aaltogamers/AG_web/contents/src/content/leaderboard.md",
        data=json.dumps(data),
        headers=headers,
    )


threePointParticipants: list[discord.member.Member] = []
twoPointParticipants: list[discord.member.Member] = []
onePointsParticipants: list[discord.member.Member] = []
allParticipants: list[discord.member.Member] = []
messageId = []


class Select(discord.ui.Select):
    def __init__(
        self,
        members: list[discord.member.Member],
        text: str,
        callbackFunction,
        selectedByDefault: bool = False,
    ):
        optionElems: list[discord.SelectOption] = []
        self.callbackFunction = callbackFunction
        for member in members:
            optionElems.append(
                discord.SelectOption(
                    label=member.display_name,
                    default=selectedByDefault,
                    value=member.id.__str__(),
                )
            )
        super().__init__(
            placeholder=text,
            max_values=members.__len__(),
            min_values=0,
            options=optionElems,
        )

    async def callback(self, interaction: discord.Interaction):
        members = []
        guild = getGuild()
        for value in self.values:
            members.append(guild.get_member(int(value)))
        await self.callbackFunction(members)
        message = await interaction.channel.fetch_message(messageId[0])  # type: ignore
        await message.edit(
            content=f"Scores to be addded to the Biweekly Leaderboard:\n{getParticipantString()}"
        )
        await interaction.response.defer()


def getParticipantString():
    participantString = ""
    participantsAndScores: dict[str, int] = {}

    for participant in allParticipants:
        participantsAndScores[participant.display_name] = 1
    for participant in onePointsParticipants:
        participantsAndScores[participant.display_name] = 2
    for participant in twoPointParticipants:
        participantsAndScores[participant.display_name] = 3
    for participant in threePointParticipants:
        participantsAndScores[participant.display_name] = 4
    for name, score in sorted(participantsAndScores.items(), key=lambda x: -x[1]):
        participantString += f"{name}: {score}\n"
    return participantString


def getparticipantIdsAndScores():
    participantsAndScores: dict[int, int] = {}

    for participant in allParticipants:
        participantsAndScores[participant.id] = 1
    for participant in onePointsParticipants:
        participantsAndScores[participant.id] = 2
    for participant in twoPointParticipants:
        participantsAndScores[participant.id] = 3
    for participant in threePointParticipants:
        participantsAndScores[participant.id] = 4

    return participantsAndScores


def updateNamesToDCNames(fileContent):
    guild = getGuild()
    for entry in fileContent["learderboard_entries"]:
        discordId = entry["discord_user_id"]
        member = guild.get_member(discordId)
        if member is not None:
            entry["name"] = member.display_name


class Button(discord.ui.Button):
    def __init__(
        self,
    ):
        super().__init__(label="Update Leaderboard", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        currentTime = datetime.datetime.now()
        currentDate = f"{currentTime.day}.{currentTime.month}.{currentTime.year}"
        participantsAndScores = getparticipantIdsAndScores()
        fileContent, sha = getFileContentAndSha()
        for entry in fileContent["learderboard_entries"]:
            discordId = entry["discord_user_id"]
            scoreToAdd = participantsAndScores.get(discordId)
            if scoreToAdd is not None:
                entry["point_entries"].append(
                    {"points": scoreToAdd, "points_acquired_on": currentDate}
                )
                participantsAndScores.pop(discordId)
        guild = getGuild()
        for discordId, score in participantsAndScores.items():
            entry = {}
            entry["name"] = guild.get_member(discordId).display_name  # type: ignore
            entry["discord_user_id"] = discordId
            entry["point_entries"] = [
                {"points": score, "points_acquired_on": currentDate}
            ]
            fileContent["learderboard_entries"].append(entry)
        updateNamesToDCNames(fileContent)

        message = await interaction.channel.fetch_message(messageId[0])  # type: ignore
        await message.edit(
            content=f"Scores that were addded to the Biweekly Leaderboard:\n{getParticipantString()}"
        )
        await interaction.response.edit_message(
            content="Leaderboard updated!", view=None
        )


class SelectView(discord.ui.View):
    def __init__(
        self,
        items: list[discord.ui.Item],
    ):
        super().__init__()

        for item in items:
            self.add_item(item)


@client.tree.command(description="Fix leaderboard")
async def fixleaderboard(interaction: discord.Interaction):
    fileContent, sha = getFileContentAndSha()
    guild = getGuild()

    for member in guild.members:
        for entry in fileContent["learderboard_entries"]:
            discordId = entry["discord_user_id"].__str__()
            if member.id.__str__()[:-4] == discordId[:-4]:
                entry["discord_user_id"] = member.id.__str__()

    newLeaderboardEntries = []
    goneTroughIds = set()

    for entry in fileContent["learderboard_entries"]:
        if entry["discord_user_id"] in goneTroughIds:
            for newEntry in newLeaderboardEntries:
                if entry["discord_user_id"] == newEntry["discord_user_id"]:
                    newEntry["point_entries"].extend(entry["point_entries"])
                    break
        else:
            goneTroughIds.add(entry["discord_user_id"])
            newLeaderboardEntries.append(entry)

    fileContent["learderboard_entries"] = newLeaderboardEntries

    commitFileContent(fileContent, sha)

    await interaction.response.send_message(content="Leaderboard fixed!")


@client.tree.command(description="Get the current status of the Biweekly Leaderboard")
async def leaderboard(interaction: discord.Interaction):
    fileContent, _ = getFileContentAndSha()
    leaderboardString = ""
    leaderboardMap = {}
    for entry in fileContent["learderboard_entries"]:
        name = entry["name"]
        points = 0
        for pointEntry in entry["point_entries"]:
            points += pointEntry["points"]
        leaderboardMap[name] = points
    i = 0
    for name, score in sorted(leaderboardMap.items(), key=lambda x: -x[1]):
        if i == 0:
            leaderboardString += ":crown:"
        elif i == 1:
            leaderboardString += ":second_place:"
        elif i == 2:
            leaderboardString += ":third_place:"
        else:
            leaderboardString += "       "
        leaderboardString += f"{name}: {score}\n"
        i += 1
    await interaction.response.send_message(
        content=f"Biweekly leaderboard:\n{leaderboardString}"
    )


@client.tree.command(
    description="Update the Biweekly Leaderboard. Only for AG Board Members"
)
async def leaderboard_update(interaction: discord.Interaction):
    guild = getGuild()
    boardRole = guild.get_role(
        1064644309669920818 if IS_DEV_MODE else 287873774852767745
    )
    # if not IS_DEV_MODE :
    caller = guild.get_member(interaction.user.id)
    if caller is None or caller.voice is None or caller.voice.channel is None:
        await interaction.response.send_message(
            "You need to be in a voice channel to use this command!"
        )
        return
    if boardRole not in caller.roles:
        await interaction.response.send_message(
            "This command is only for board members!"
        )
        return
    voiceChannel = caller.voice.channel
    voiceChannelMembers = voiceChannel.members
    allParticipants.clear()
    threePointParticipants.clear()
    twoPointParticipants.clear()
    onePointsParticipants.clear()
    allParticipants.extend(voiceChannelMembers)

    async def participantCallback(members):
        allParticipants.clear()
        allParticipants.extend(members)

    async def threeCallback(members):
        threePointParticipants.clear()
        threePointParticipants.extend(members)

    async def twoCallback(members):
        twoPointParticipants.clear()
        twoPointParticipants.extend(members)

    async def oneCallback(members):
        onePointsParticipants.clear()
        onePointsParticipants.extend(members)

    participantSelect = Select(
        members=voiceChannelMembers,
        selectedByDefault=True,
        text="Select all participants",
        callbackFunction=participantCallback,
    )
    threePointSelect = Select(
        members=voiceChannelMembers,
        selectedByDefault=False,
        text="Select participants who get 3 + 1 points",
        callbackFunction=threeCallback,
    )
    twoPointSelect = Select(
        members=voiceChannelMembers,
        selectedByDefault=False,
        text="Select participants who get 2 + 1 points",
        callbackFunction=twoCallback,
    )
    onePointSelect = Select(
        members=voiceChannelMembers,
        selectedByDefault=False,
        text="Select participants who get 1 + 1 points",
        callbackFunction=oneCallback,
    )

    button = Button()

    await interaction.response.send_message(
        content=f"Update Biweekly Leaderboard (1st select is all participants, 2nd is 3 + 1 points, 3rd is 2 + 1 points, 4th is 1 + 1 points)",
        view=SelectView(
            [
                participantSelect,
                threePointSelect,
                twoPointSelect,
                onePointSelect,
                button,
            ]
        ),
        ephemeral=True,
    )
    messageRes = await interaction.channel.send(  # type: ignore
        content=f"Scores to be addded to the Biweekly Leaderboard:\n{getParticipantString()}",
    )
    messageId.clear()
    messageId.append(messageRes.id)
