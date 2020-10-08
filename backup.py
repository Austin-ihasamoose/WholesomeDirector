"""
    Author: moose
    Description: This is a simple queue bot, based off Among Us
"""

import asyncio
import os
from dotenv import load_dotenv
from discord.ext import commands, tasks
import discord

''' 
    TO DO:
    Complete: When both voice channels are empty, clear the queue.
    Fix bump manager
    if ping happens, check for leave commands, check if voice channel has been joined by them
'''

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BOT_COLOR = 0x0D61B7

bot = commands.Bot(command_prefix='!q ', case_insensitive=True)
bot.remove_command('help')

user_bump_count = []
lobby_footer = None
ping_active = False
pinged_user = None


class Queue:
    def __init__(self, queue=None, timeout=180, capacity=10):
        self.queue = [] if queue is None else queue
        self.timeout = timeout
        self.capacity = capacity

    def is_full(self):
        return len(self.queue) == self.capacity

    def is_empty(self):
        if self.queue is None:
            return True
        return False

    def append(self, name):
        self.queue.append(name)
        return

    def __str__(self):
        if self.queue is None:
            return "Queue is empty."
        else:
            return str(self.queue)


q = Queue()


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
        ping_active = False
        q.queue.remove(ctx.author)
        return await ctx.send(f'{ctx.author.mention} left the queue while ping was active for them.\n'
                              f'They were removed from the queue, and ping request cancelled..')

    q.queue.remove(ctx.author)

    return await ctx.send(f'{ctx.author.mention} left the queue.')


@bot.command(name='show')
async def print_embed(ctx):
    global lobby_footer
    title = f'{len(q.queue)}/{q.capacity}'

    if q.queue:
        body = ''
        for i in range(len(q.queue)):
            body += str(i + 1) + ": " + str(q.queue[i].name) + '\n'
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
        ping_active = False
        return await ctx.send(f'Removed {mentioned_user.name} from the queue while they were being pinged.\n'
                              f'They have been removed, and ping request cancelled.')

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
                    f'Cancelled ping request for {pinged_user.name}')
                ping_active = False


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
                    f'Cancelled ping request for {pinged_user.name}')
                ping_active = False


@bot.command(name='clear')
@commands.has_any_role(751675874323071026,
                       755229009809375233,
                       751675798326345818,
                       751675847852949534)
async def clear(log=True):
    channel = bot.get_channel(757316465438359593)
    if len(q.queue) == 0:
        if log:
            return await channel.send(f'The queue is already empty. Request denied.')
    if len(q.queue) > 0:
        q.queue = []
        if log:
            return await channel.send(f'The queue has been cleared.')
        return


@bot.command(name='ping')
async def ping(ctx):
    global ping_active, pinged_user
    if not ping_active:
        ping_active = True

        def check(m):
            if len(q.queue) > 0:
                return m.author == q.queue[0] and m.content == '!accept'
            else:
                return False

        async def check_if_joined():
            channel = bot.get_channel(757316465438359593)
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

            for member in members:
                for m in members[member]:
                    if m.name == pinged_user.name:
                        return True

            return False

        if len(q.queue) > 0:
            pinged_user = q.queue[0]
            await ctx.send(f'Pinging next user via DMs and chat! '
                           f"{pinged_user.mention}, you're up to play! "
                           f"Please type !accept in chat within "
                           f"the next 1.5 minutes, or you will be bumped back.")

            try:
                await pinged_user.create_dm()
                await pinged_user.send(f"{pinged_user.mention}, you're up to play! Please type !accept in the chat within "
                                       f"the next 1.5 minutes, or you will be bumped back.")

            except Exception as e:
                print(pinged_user, e)
                pass

            try:
                await bot.wait_for('message', timeout=90, check=check)
                q.queue.pop(0)
                if q is not None:
                    await ctx.send(f'{pinged_user.name} accepted the ping! Updating queue...')
                    ping_active = False
                    pinged_user = None
            except asyncio.TimeoutError:
                if ping_active and not q.is_empty():
                    temp = q.queue.pop(0)
                    q.queue.insert(1, temp)
                    joined = await check_if_joined()
                    if joined:
                        q.queue.pop(0)
                        await ctx.send(f'{pinged_user.name} joined the channel while pinged. Removed from queue.')
                        ping_active = False
                        pinged_user = None
                        return
                    await ctx.send(f'{pinged_user.name} never accepted the ping after 1.5 minutes.'
                                   f' Bumped back in queue.')
                    await pinged_user.create_dm()
                    await pinged_user.send(f"You failed to accept the ping, and have been bumped back in the queue.")
                    ping_active = False
                    pinged_user = None
                else:
                    await ctx.send("Ping isn't active, or queue is empty.")

        else:
            await ctx.send("There is nobody in the queue to ping.")
            ping_active = False
            return
    else:
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
            await clear(log=False)
            return await channel.send('Server detected as inactive. Queue has been cleared.')

        await asyncio.sleep(10)


bot.run(TOKEN)
