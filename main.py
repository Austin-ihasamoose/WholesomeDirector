"""
    Author: moose
    Description: This is a simple queue bot, based off Among Us
"""



















''' THIS IS LIVE'''

































import asyncio
import os
import random

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

''' 
    TO DO:
    (SHOULD BE FIXED)!q random (generates two random lobbies based on people in both channels. both channels must be full for this to work)
    (SHOULD BE FIXED) !q ping bump manager (remove ppl from queue when they miss two consecutive pings)
    (SHOULD BE FIXED) !q ping (fix wrong removals (pop.queue[0] to for loop))
    (SHOULD BE FIXED) !q ping (on message, send code and put code in chat)
    (SHOULD BE FIXED) !q show (if they have nickname in server, use that.)
    (SHOULD BE FIXED) !q clear (clear lobby footer if there's no queue)
    !q watch list manager
'''

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BOT_COLOR = 0x0D61B7

bot = commands.Bot(command_prefix='!q ', case_insensitive=True)
bot.remove_command('help')

user_bump_count = {}
lobby_footer = None
ping_active = False
pinged_user = None


class Queue:
    def __init__(self, queue=None, timeout=180, capacity=10, colour=None):
        self.queue = [] if queue is None else queue
        self.timeout = timeout
        self.capacity = capacity
        self.colour = colour

    def is_full(self):
        return len(self.queue) == self.capacity

    def is_empty(self):
        if self.queue is None:
            return True
        return False

    def append(self, name):
        self.queue.append(name)

    def __str__(self):
        if self.queue is None:
            return "Queue is empty."
        else:
            return str(self.queue)


q = Queue()


def flatten(L):
    if type(L) is not list:
        return
    if len(L) == 0:
        return
    if len(L) == 1:
        if type(L[0]) == list:
            result = flatten(L[0])
        else:
            result = L

    elif type(L[0]) == list:
        result = flatten(L[0]) + flatten(L[1:])
    else:
        result = [L[0]] + flatten(L[1:])

    return result


@bot.command(name='randomize')
async def randomize(ctx):
    print('a')
    channel = bot.get_channel(757316465438359593)
    channel_one = bot.get_channel(750684949056847925)
    channel_two = bot.get_channel(753633089288142869)

    channels = [channel_one, channel_two]
    members = {}
    all_members = []
    randomized_members = []

    if not channel_one or not channel_two:
        # if either channels don't exist message moosinator
        return await channel.send('Channels do not exist! Message @moose please.')

    for ch in channels:
        members.setdefault(ch.id, [])
        for member in ch.members:
            if member.nick is not None:
                members[ch.id].append(member.nick)
            else:
                members[ch.id].append(member.name)

    for value in members:
        all_members.append(members[value])

    all_members = flatten(all_members)

    if len(all_members) < 20:
        return await channel.send("Randomize request denied, need two full lobbies (20 ppl) to randomize.")

    if isinstance(all_members, list):
        while len(all_members) > 0:
            random_member = all_members.pop((random.randint(0, len(all_members))) - 1)
            randomized_members.append(random_member)

        return await channel.send(f'New Lobby 1 generation: \n'
                                  f'{"".join(randomized_members[0])}, '
                                  f'{",".join(randomized_members[1:10])}\n'
                                  f'New Lobby 2 generation: \n'
                                  f'{"".join(randomized_members[10])}, '
                                  f'{"".join(randomized_members[11:20])},')

    else:
        return ctx.send('somethin borked.')


@bot.command(name='join')
async def join(ctx):
    if ctx.author in q.queue:
        return await ctx.send(f'{ctx.author.mention} is already in the queue.')
    if q.is_full():
        return await ctx.send(f'Queue is full. Request denied.')

    q.append(ctx.author)

    return await ctx.send(f' {ctx.author.mention} joined the queue.'
                          f'\nTo see current queue, type: !q show')


@bot.command(name='leave')
async def leave(ctx):
    global ping_active

    if q.is_empty():
        return await ctx.send(f'Queue is empty. Request denied.')
    if ctx.author not in q.queue:
        return await ctx.send(f"{ctx.author.mention} isn't in the queue. Request denied.")

    if ping_active:
        q.queue.remove(ctx.author)
        return await ctx.send(f'{ctx.author.mention} left the queue while a ping was active.\n'
                              f'They were removed from the queue. Please wait for ping to complete prior to pinging '
                              f'another user.')

    q.queue.remove(ctx.author)

    return await ctx.send(f'{ctx.author.mention} left the queue.')


@bot.command(name='show')
async def print_embed(ctx):
    global lobby_footer
    title = f'{len(q.queue)}/{q.capacity}'

    if q.queue:
        body = ''
        for i in range(len(q.queue)):
            if q.queue[i].nick is not None:
                stringable_name = q.queue[i].nick
            else:
                stringable_name = q.queue[i].name
            body += str(i + 1) + ": " + str(stringable_name) + '\n'
    else:
        body = 'Queue is empty.'

    embed = discord.Embed(title='Current Queue: ' + title, description=body, color=discord.Colour.dark_blue())

    if lobby_footer is not None:
        embed.set_footer(text=lobby_footer)

    await ctx.send(embed=embed)


@bot.command(name='remove')
@commands.has_any_role(751675874323071026,
                       755229009809375233,
                       751675798326345818)
async def remove(ctx):
    global ping_active

    if len(ctx.message.mentions) == 0:
        return print(f"No user mentioned!")

    if q.is_empty():
        return await ctx.send(f'Queue is empty. Request denied.')

    mentioned_user = ctx.message.mentions[0]

    if mentioned_user in q.queue:
        q.queue.remove(mentioned_user)
    else:
        return await ctx.send(f'@{mentioned_user} is not in the queue.')

    if ping_active:
        return await ctx.send(f'Removed {mentioned_user.name} from the queue while they were being pinged.\n'
                              f'They have been removed, please wait for ping to complete prior to pinging '
                              f'another user.')

    return await ctx.send(f'Removed {mentioned_user.name} from the queue.')


@bot.command(name='add')
@commands.has_any_role(751675874323071026,
                       755229009809375233,
                       751675798326345818)
async def add(ctx):
    if len(ctx.message.mentions) == 0:
        return print(f"No user mentioned!")
    else:
        mentioned_user = ctx.message.mentions[0]
        if mentioned_user in q.queue:
            return await ctx.send(f'User is already in the queue. Request denied.')
        if q.is_full():
            return await ctx.send(f'Queue is full. Request denied.')

        q.queue.append(mentioned_user)
        return await ctx.send(f' {mentioned_user.name} was added to the queue.'
                              f'\nTo see current queue, type: !q show')


@bot.command(name='moveup')
@commands.has_any_role(751675874323071026,
                       755229009809375233,
                       751675798326345818)
async def move_up(ctx):
    global ping_active, pinged_user
    if not ping_active:
        if len(ctx.message.mentions) == 0:
            return print(f"No user mentioned!")
        else:
            mentioned_user = ctx.message.mentions[0]
            position = None
            if mentioned_user not in q.queue:
                return await ctx.send(f'@{mentioned_user.name} is not in the queue.')

            for i in range(len(q.queue)):
                if q.queue[i] == mentioned_user:
                    position = i
                    break
            if position == 0:
                return await ctx.send(f' {mentioned_user.name} is already at the front of the queue. Request denied.')
            else:
                current_user_placement = q.queue.pop(position)
                q.queue.insert(position - 1, current_user_placement)

            return await ctx.send(f' {mentioned_user.name} was bumped up from position: {position + 1} to {position}')
    else:
        if pinged_user:
            if q.is_empty() is False:
                for i in range(len(q.queue)):
                    if q.queue[i] == pinged_user:
                        user_above = q.queue[i - 1]
                        break

            print(user_above.name)
            print(ctx.message.mentions[0].name)
            print(user_above.name == ctx.message.mentions[0].name)

            if len(ctx.message.mentions) == 0:
                return print(f"No user mentioned!")
            else:
                # elif user_above.name == ctx.message.mentions[0].name:
                print('test')
                mentioned_user = ctx.message.mentions[0]
                position = None
                if mentioned_user not in q.queue:
                    return await ctx.send(f'@{mentioned_user.name} is not in the queue.')

                for i in range(len(q.queue)):
                    if q.queue[i] == mentioned_user:
                        position = i
                        break
                if position == 0:
                    return await ctx.send(
                        f' {mentioned_user.name} is already at the front of the queue. Request denied.')
                else:
                    current_user_placement = q.queue.pop(position)
                    q.queue.insert(position - 1, current_user_placement)

                await ctx.send(
                    f'{mentioned_user.name} was bumped up from position: {position + 1} to {position}\n'
                    f'There was a ping active when they were removed. Please wait until it completes prior to '
                    f'pinging another user.')


@bot.command(name='movedown')
@commands.has_any_role(751675874323071026,
                       755229009809375233,
                       751675798326345818)
async def move_down(ctx):
    global ping_active, pinged_user
    if not ping_active:
        if len(ctx.message.mentions) == 0:
            return print(f"No user mentioned!")
        else:
            mentioned_user = ctx.message.mentions[0]
            position = None
            if mentioned_user not in q.queue:
                return await ctx.send(f'@{mentioned_user.name} is not in the queue.')

            for i in range(len(q.queue)):
                if q.queue[i] == mentioned_user:
                    position = i
                    break
            if position == (len(q.queue) - 1):
                return await ctx.send(f' {mentioned_user.name} is already at the back of the queue. Request denied.')
            else:
                current_user_placement = q.queue.pop(position)
                q.queue.insert(position + 1, current_user_placement)

            return await ctx.send(
                f' {mentioned_user.name} was bumped up from position: {position + 1} to {position + 2}')
    else:
        if pinged_user:
            if q.is_empty() is False:
                for i in range(len(q.queue)):
                    if q.queue[i] == pinged_user:
                        user_below = q.queue[i + 1]
                        break

            print(user_below.name)
            print(ctx.message.mentions[0].name)
            print(user_below.name == ctx.message.mentions[0].name)

            if len(ctx.message.mentions) == 0:
                return print(f"No user mentioned!")
            else:
                # elif user_below.name == ctx.message.mentions[0].name:
                print('test')
                mentioned_user = ctx.message.mentions[0]
                position = None
                if mentioned_user not in q.queue:
                    return await ctx.send(f'@{mentioned_user.name} is not in the queue.')

                for i in range(len(q.queue)):
                    if q.queue[i] == mentioned_user:
                        position = i
                        break
                if position == (len(q.queue) - 1):
                    return await ctx.send(
                        f' {mentioned_user.name} is already at the back of the queue. Request denied.')
                else:
                    current_user_placement = q.queue.pop(position)
                    q.queue.insert(position + 1, current_user_placement)

                await ctx.send(
                    f'{mentioned_user.name} was bumped up from position: {position + 1} to {position + 2}\n'
                    f'There was a ping active when they were removed. Please wait until it completes prior to '
                    f'pinging another user.')


@bot.command(name='clear')
@commands.has_any_role(751675874323071026,
                       755229009809375233,
                       751675798326345818,
                       751675847852949534)
async def clear(log=True):
    global lobby_footer
    channel = bot.get_channel(757316465438359593)
    if len(q.queue) == 0:
        if lobby_footer is not None:
            lobby_footer = None
            return await channel.send('Cleared lobby code, but the queue was empty already.')
        if log:
            return await channel.send(f'The queue is already empty. Request denied.')
    if len(q.queue) > 0:
        q.queue = []
        if log:
            return await channel.send(f'The queue has been cleared.')
        return


@bot.command(name='ping')
async def ping(ctx):
    global ping_active, pinged_user, user_bump_count, lobby_footer
    print(ping_active)
    if not ping_active:
        print('a')
        ping_active = True

        def check(m):
            print('b')
            if len(q.queue) > 0:
                return m.author == q.queue[0] and m.content == '!accept'
            else:
                return False

        async def check_if_joined():
            print('c')
            channel = bot.get_channel(757316465438359593)
            channel_one = bot.get_channel(750684949056847925)
            channel_two = bot.get_channel(753633089288142869)

            channels = [channel_one, channel_two]
            members = {}
            i = 0
            if not channel_one or not channel_two:
                print('d')
                return await channel.send('Channels do not exist! Message @moose please.')

            for ch in channels:
                members[i] = ch.members
                i += 1

            for member in members:
                for m in members[member]:
                    if m.name == pinged_user.name:
                        print('e')
                        return True
            print('f')
            return False

        if len(q.queue) > 0:
            print('g')
            pinged_user = q.queue[0]
            await ctx.send(f'Pinging next user via DMs and chat! '
                           f"{pinged_user.mention}, you're up to play! "
                           f"Please type !accept in chat within "
                           f"the next 1.5 minutes, or you will be bumped back.\n"
                           f"Current game information: {lobby_footer}")

            try:
                print('h')
                await pinged_user.create_dm()
                await pinged_user.send(f"{pinged_user.mention}, you're up to play!"
                                       f" Please type !accept in the chat within "
                                       f"the next 1.5 minutes, or you will be bumped back.\n"
                                       f"Current game information: {lobby_footer}")

            except Exception as e:
                print('i')
                print(pinged_user, e)

            try:
                print('j')
                print(q.queue)
                await bot.wait_for('message', timeout=90, check=check)
                print(len(q.queue))
                if q is not None:
                    print('L')
                    await ctx.send(f'{pinged_user.name} accepted the ping! Updating queue...')
                    for i in range(len(q.queue)):
                        print(i)
                        print(q.queue[i])
                        print(pinged_user)
                        if q.queue[i] == pinged_user:
                            print('k')
                            q.queue.remove(q.queue[i])
                    ping_active = False
                    pinged_user = None
            except asyncio.TimeoutError:
                print('o')
                if ping_active and not q.is_empty():
                    print('p')
                    temp = q.queue.pop(0)
                    q.queue.insert(1, temp)
                    joined = await check_if_joined()
                    if joined:
                        print('q')
                        for i in range(len(q.queue)):
                            if q.queue[i] == pinged_user:
                                q.queue.remove(q.queue[i])
                                await ctx.send(f'{pinged_user.name} joined the channel while pinged.'
                                               f' Removed from queue.')
                                ping_active = False
                                pinged_user = None
                                return

                    user_bump_count.setdefault(pinged_user.name, 0)
                    if user_bump_count[pinged_user.name] < 2:
                        print('r')
                        user_bump_count[pinged_user.name] += 1
                        await ctx.send(f'{pinged_user.name} never accepted the ping after 1.5 minutes.'
                                       f' Bumped back in queue.')
                        await pinged_user.create_dm()
                        await pinged_user.send(
                            f"You failed to accept the ping, and have been bumped back in the queue.")
                        ping_active = False
                        pinged_user = None
                        return
                    elif user_bump_count[pinged_user.name] == 2:
                        print('s')
                        print('hit the road, jack')
                        for i in range(len(q.queue)):
                            if q.queue[i] == pinged_user:
                                print('k3')
                                q.queue.remove(q.queue[i])
                                user_bump_count[pinged_user.name] = 0

                        ping_active = False
                        pinged_user = None

                        return await ctx.send(f'{pinged_user.name} never accepted the ping after two attempts.'
                                              f' Kicked them from queue.')

                else:
                    print('t')
                    ping_active = False
                    pinged_user = None
                    await ctx.send("Ping isn't active, or queue is empty.")

        else:
            print('u')
            await ctx.send("There is nobody in the queue to ping.")
            ping_active = False
            return
    else:
        print('v')
        await ctx.send("There is already a ping active. Please wait until it completes.")


@bot.command(name='lobby')
async def lobby_info(ctx):
    global lobby_footer
    msg = ctx.message.content
    split_msg = msg.split()
    if len(split_msg) == 4:
        region = split_msg[2]
        if len(region) > 2:
            await ctx.send(f'Incorrect format for lobby command.\nCorrect usage: !q lobby <REGION> <CODE>\n'
                           f'Region must be TWO characters, lobby five or six.')
            return
        code = split_msg[3]
        if len(code) <= 3 or len(code) >= 7:
            await ctx.send(f'Incorrect format for lobby command.\nCorrect usage: !q lobby <REGION> <CODE>\n'
                           f'Region must be TWO characters, lobby five or six.')
            return
        lobby_footer = f'Region: {region.upper()}\n' \
                       f'Code: {code.upper()}'
        await ctx.send(f'Set the region and code successfully.')
        return lobby_footer
    else:
        await ctx.send(f'Incorrect format for lobby command.\nCorrect usage: !q lobby <REGION> <CODE>\n'
                       f'Region must be TWO characters, lobby 4/5/6.')


@bot.command(name='help')
async def help(ctx):
    embed = discord.Embed(title="Queue Bot Helper",
                          description="**!q join** Adds yourself to queue\n"
                                      "**!q leave** Removes yourself from queue\n"
                                      "**!q show** Displays queue\n"
                                      "**!q lobby <region> <code>** Set !q show's lobby footer to show region/code.\n"
                                      "**!q randomize** randomize lobbies 1 and 2 and display a list of randomized"
                                      " users. This ONLY works when there is 10 people in each lobby, and does NOT "
                                      "mutate the queue in any form.\n"
                                      "**!q add <mention>** (Role Blurbry+) add user to queue. ex. !q add @ihasamoose\n"
                                      "**!q remove <mention>** (Role Blurbry+) remove user from queue.\n"
                                      "**!q moveup <mention>** (Role Blurbry+) move user forward in queue.\n"
                                      "**!q movedown <mention>** (Role Blurbry+) move user back in queue.\n"
                                      "**!q clear** (Role Blurbry+) clear entire queue.\n"
                                      "**!q ping** (Role Blurbry+) will ping next user up to play. \n"
                                      "They must type !accept to accept the ping, and the user will be removed "
                                      "them from the queue.",
                          color=discord.Colour.dark_blue())
    await ctx.send(embed=embed)


@bot.event
async def on_message(message):
    if message.channel.id == 757316465438359593:
        await bot.process_commands(message)


@bot.event
async def on_ready():
    game = discord.Game("The Game")
    check_channel.start()
    await bot.change_presence(status=discord.Status.online, activity=game, afk=False)


@tasks.loop(minutes=60)
async def check_channel():
    channel = bot.get_channel(757316465438359593)

    async for message in channel.history(limit=5):
        if message.author.name == "Wholesome Director" and message.content.startswith('Server detected'):
            return

    while True:
        channel_one = bot.get_channel(750684949056847925)
        channel_two = bot.get_channel(753633089288142869)

        channels = [channel_one, channel_two]
        members = {}
        i = 0
        if not channel_one or not channel_two:
            return await channel.send('Channels do not exist! Message @moose please.')

        for ch in channels:
            members[i] = ch.members
            i += 1

        if len(members[0]) == 0 and len(members[1]) == 0:
            if len(q.queue) > 0 or lobby_footer is not None:
                await clear(log=False)
                return await channel.send('Server detected as inactive. Queue has been cleared.')

        await asyncio.sleep(10)


bot.run(TOKEN)
