import discord
import re
from .setup import (
    client,
    getGuild,
    roleMessageId,
    roleChannelId,
    errorMessageChannnelId,
    traceErrorAndSendErrorMessage,
)


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
