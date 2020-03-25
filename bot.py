#!/usr/bin/env python

import os
import discord
import random
from discord.ext import commands

if os.getenv('HEROKU') is None:
    print('Loading debug environment!')
    from dotenv import load_dotenv
    load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

client = commands.Bot(command_prefix='!')

ROLES = {
    'KING': {
        'title': 'King',
        'description': 'You are the king! Your life total starts at 50, you begin the game, and you win if you, or you and the knight, are the last members standing',
        'color': 0xEEEEEE,
        'thumbnail': 'https://static.thenounproject.com/png/382020-200.png'
    },
    'KNIGHT': {
        'title': 'Knight',
        'description': 'You are the knight! Your sole objective is protecting the King. If the King wins, you win, even if you are dead',
        'color': 0x00FF00,
        'thumbnail': 'https://static.thenounproject.com/png/440140-200.png'
    },
    'BANDIT': {
        'title': 'Bandit',
        'description': "You are a bandit! If the king dies, and it was not because of the usurper, you win!",
        'color': 0xFF0000,
        'thumbnail': 'https://static.thenounproject.com/png/79853-200.png'
    },
    'ASSASSIN': {
        'title': 'Assassin',
        'description': "You are the assassin! You want the king dead, but you know that you are too weak to take the crown for yourself while the Bandits are still alive. Make sure the Bandits are dead, then kill the King and win!",
        'color': 0x000000,
        'thumbnail': 'https://static.thenounproject.com/png/1214-200.png'
    },
    'USURPER': {
        'title': 'Usurper',
        'description': "You are the usurper! If the king dies by your hand, you become the new king, your life total goes to 50 (if it was lower than 50), and you now win if you and the knight are the last ones standing",
        'color': 0x0000FF,
        'thumbnail': 'https://steemitimages.com/DQmZDnnuhnc67zBNVurMhGY9xa3abVHTwanhDTvZSw6Wni6/84490-200.png'
    }
}

GOALS = {
    'KING': 'One king. Starts at 50 life. Goes first. Wins when only himself or himself and the knight are the last players alive *(PLAINS/WHITE)*',
    'KNIGHT': 'One knight. Wins when the king wins. If the Knight dies but the King still wins, the knight wins. *(FOREST/GREEN)*',
    'BANDIT': 'Two bandits. If the king dies while a bandit is alive (and not due to the usurper), the bandits win. *(MOUTAIN/RED)*',
    'ASSASSIN': 'One assassin. Wins when the king dies, if all bandits are dead (not due to the usurper). This role often looks like a knight, because he wants the bandits dead. *(SWAMP/BLACK)*',
    'USURPER': 'One usurper. If the usurper kills the king, he becomes the king, his life total goes to 50, and he now wins the way kings win. This role often looks like a bandit, because he wants the bandits to let him land the killing blow. *(ISLAND/BLUE)*'
}


def create_rules_embed(num_players):
    if (num_players == 5):
        ROLES = ['KING', 'KNIGHT', 'BANDIT', 'ASSASSIN']
    else:
        ROLES = ['KING', 'KNIGHT', 'BANDIT', 'ASSASSIN', 'USURPER']

    lines = []
    for role in ROLES:
        lines.append(f'**{role}**: {GOALS[role]}')

    description = '\n\n'.join(lines)

    return discord.Embed(title="Roles", description=description)


@client.event
async def on_ready():
    print('Bot started')


async def send_roles(ctx):
    print('Author is: ', ctx.author)
    return await ctx.author.send('Roles sent!')


async def send_about(ctx):
    about = '''
Kingdoms is an EDH variant based on hidden roles, intended to be played with 5 or 6 players.
Games work best when players use decks that can interact with, and deal damage to, individual players.
Decks which win through combo, or decks which shut down combat, are not encouraged.

To create a new game, use `!kingdoms new <players>`
i.e `!kingdoms new @player1 @player2 @player3 @player4 @player5`

If you wish to prevent someone from being king, you can use the alternate syntax:
`!kingdoms new <eligible king players> -- <non-king players>`
i.e. `!kingdoms new @player2 @player3 @player4 -- @player1 @player5`
would ensure that both player1 and player5 are not king
    '''
    return await ctx.author.send(about)


async def new_game(ctx, *args):
    num_players = len([arg for arg in args if arg != SEPARATOR])
    if num_players < 5 or num_players > 6:
        return await ctx.send(f'**ERROR**! Invalid number of players: {num_players}. Kingdoms can only be played with 5 or 6 players.')

    converter = commands.MemberConverter()

    real_users = []
    invalid_users = []
    for arg in args:
        if arg == SEPARATOR:
            real_users.append(arg)
        else:
            if not await is_valid_user(ctx, arg):
                invalid_users.append(arg)
            # try:
            #     await converter.convert(ctx, arg)
            # except Exception:
            #     invalid_users.append(arg)

    if len(invalid_users) > 0:
        return await ctx.send(
            f'Invalid users specified: {", ".join(invalid_users)}. Please specify discord users on this server, using the `@User` syntax')

    real_users = [await converter.convert(ctx, user) if user != SEPARATOR else SEPARATOR for user in args]

    roles = assign_users(real_users)
    king = next(user for user in roles if roles[user] == 'KING')
    rules = create_rules_embed(num_players)

    for user in roles:
        role = ROLES[roles[user]]
        e = discord.Embed(
            title=role['title'], description=role['description'], color=role['color'])
        e.set_thumbnail(
            url=role['thumbnail'])
        await user.send(embed=e)
        await user.send(embed=rules)

    await ctx.send(f'{king.mention} is the King! Long live the King!')


async def is_valid_user(ctx, user_name):
    converter = commands.MemberConverter()
    try:
        await converter.convert(ctx, user_name)
        return True
    except Exception:
        return False

HELP_MESSAGE = 'Please use "!kingdoms about" for more information'
ERROR_MESSAGE = f'Invalid command specified. {HELP_MESSAGE}'


@client.command(name='kingdoms')
async def kingdoms(ctx, *args):
    if len(args) == 0:
        return await ctx.send(ERROR_MESSAGE)

    command = args[0]
    if command.lower() == 'about':
        await send_about(ctx)
        return
    elif command.lower() == 'new':
        await new_game(ctx, *args[1:])
        return
    else:
        if await is_valid_user(ctx, command):
            return await new_game(ctx, *args)
        else:
            return await ctx.send(ERROR_MESSAGE)

kingdoms.__doc__ = HELP_MESSAGE

SEPARATOR = '--'
NOT_FOUND = -1


def create_roles_output(roles):
    lines = []
    for key in roles:
        lines.append(f'{key}: {roles[key]}')

    return '\n'.join(lines)


def assign_users(users):
    separator_index = get_index_of(users, SEPARATOR)
    roles = None
    if separator_index != NOT_FOUND:
        king_eligible_users = users[0:separator_index]
        unassigned_users = users[separator_index + 1:]
        king, other_users = separate_king_and_others(king_eligible_users)
        unassigned_users = other_users + unassigned_users
        roles = assign_other_roles(unassigned_users)
        roles[king] = 'KING'
    else:
        king, other_users = separate_king_and_others(users)
        roles = assign_other_roles(other_users)
        roles[king] = 'KING'

    return roles


def separate_king_and_others(users):
    king_index = random.randrange(0, len(users))
    king = users[king_index]
    others = users[0:king_index] + users[king_index + 1:]

    return king, others


def assign_other_roles(users):
    num_users = len(users)
    if num_users < 4 or num_users > 5:
        raise ValueError(f'invalid number of users: {num_users}')

    if num_users == 4:
        roles = ['KNIGHT', 'BANDIT', 'BANDIT', 'ASSASSIN']
    else:
        roles = ['KNIGHT', 'BANDIT', 'BANDIT', 'ASSASSIN', 'USURPER']

    random.shuffle(roles)
    return dict(zip(users, roles))


def get_index_of(list, target):
    try:
        return list.index(target)
    except ValueError:
        return -1


client.run(TOKEN)
