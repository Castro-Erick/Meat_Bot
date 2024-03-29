import asyncio
import discord
import json
import logging
import os
import youtube_dl

from discord.ext import commands
from discord.ext import tasks
from discord import FFmpegPCMAudio
from random import randint

BOT_TOKEN = 'Place Discord Bot Token Here'

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

#prefix can be changed to something else, but is set to '!' as default
prefix = '!'
client = commands.Bot(command_prefix=prefix, intents=intents)

DEFAULT_PURGE_INTERVAL = 3600 #1 hour in seconds
PURGE_INTERVAL_FILE = 'purge_interval.json'
PURGE_LIST_FILE = 'purge_list.json'
yt_queue = []
yt_queue_title_names = []

#returns YouTube audio url and title
def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': 'best',
        }],
        'quiet': True,
    }
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']
        video_title = info.get('title', 'Unknown Title')
    
    yt_queue_title_names.append(video_title)
    
    return audio_url

#loads "purge_interval.json"
def load_purge_interval():
    if not os.path.exists(PURGE_INTERVAL_FILE):
        return DEFAULT_PURGE_INTERVAL
    try:
        with open(PURGE_INTERVAL_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return DEFAULT_PURGE_INTERVAL

#loads "purge_list.json"
def load_purge_list():
    if not os.path.exists(PURGE_LIST_FILE):
        return []
    try:
        with open(PURGE_LIST_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

#returns random meatwad clip
def meatwad():
    meatwad_clips = ["Local Directories Here", "For Sound Clips", "Originally tested with meatwad clips"]
    index = randint(0, len(meatwad_clips)-1)
    return meatwad_clips[index]

#plays the next song in the queue
def play_next(ctx) -> None:
    if not yt_queue:
        return
    
    url = yt_queue.pop(0)
    yt_queue_title_names.pop(0)
    audio_source = FFmpegPCMAudio(url)
    ctx.voice_client.play(audio_source, after=lambda e: play_next(ctx))

#saves "purge_interval.json"
def save_purge_interval(purge_interval):
    with open(PURGE_INTERVAL_FILE, 'w') as file:
        json.dump(purge_interval, file)

#saves "purge_list.json"
def save_purge_list(purge_list):
    with open(PURGE_LIST_FILE, 'w') as file:
        json.dump(purge_list, file)



#loop to purge channels of messages
@tasks.loop(seconds=purge_interval)
async def purge_messages():
    for channel_id in purge_list:
        channel = client.get_channel(channel_id)
        if channel:
            await channel.purge()



#loads purge interval on bot startup
purge_interval = load_purge_interval()

#loads purge list on bot startup
purge_list = load_purge_list()

#displays message on launch when bot is ready
@client.event
async def on_ready():
    print("MeatBot reporting for duty!")
    print("---------------------")
    purge_messages.start()



@tasks.loop(seconds=purge_interval)
async def purge_messages():
    for channel_id in purge_list:
        channel = client.get_channel(channel_id)
        if channel:
            await channel.purge()

#Displays current song
@client.command()
async def current_song(ctx):
    await ctx.send(yt_queue_title_names[0])

#Gives a list of cyber news related websites
@client.command()
async def cyber_news(ctx):
    cyber_url_list = ["https://www.bleepingcomputer.com/", "https://cyberscoop.com/", "https://www.infosecurity-magazine.com/", "https://isc.sans.edu/", "https://news.sophos.com/en-us/category/serious-security/", "https://thehackernews.com/", "https://threatpost.com/"]
    
    urls_txt = '\n'.join(cyber_url_list)
    
    await ctx.send(f'Here\'s a list of websites related to Cyber News:\n{urls_txt}')        

#flips a coin
@client.command()
async def flip(ctx):
    if randint(1,2) == 1:
        await ctx.send('heads')
    else:
        await ctx.send('tails')

#changes the frequency at which the channels on the purge list are purged
@client.command()
async def interval(ctx, new_interval: int = None):
    global purge_interval
    if new_interval is None:
        await ctx.send(f"Affected channels will be purged every {purge_interval} seconds.")
    else:
        purge_interval = new_interval
        save_purge_interval(purge_interval)
        await ctx.send(f"Default purge interval has been set to {new_interval}")

#disconnects bot from channel (always good to keep, maybe have automatic timeout eventually)
@client.command(pass_context = True)
async def leave(ctx):
    client = ctx.voice_client
    if client:
        channel = ctx.voice_client
        yt_queue.clear()
        yt_queue_title_names.clear()
        await channel.disconnect()
    else:
        await ctx.send('I\'m not in a voice channel')

#play random meatwad clips
@client.command()
async def mwad(ctx):
    if not ctx.author.voice.channel:
        await ctx.send("You are not in a voice channel.")
        return

    if not ctx.voice_client:
        voice_channel = ctx.author.voice.channel
        voice_client = await voice_channel.connect()
    else:
        voice_client = ctx.voice_client
        
    audio_source = FFmpegPCMAudio(meatwad())
    voice_client.play(audio_source)

#pauses song
@client.command()
async def pause(ctx):
    if not ctx.author.voice.channel:
        await ctx.send("You are not in the voice channel.")
    else:
        voice_client = ctx.voice_client
        voice_client.pause()

@client.command()
async def play(ctx, yt_url=None):
    #checks to see if you are in the voice channel
    try:
        if not ctx.author.voice.channel:
            await ctx.send("You are not in a voice channel.")
            return
        if yt_url == None:
            voice_client = ctx.voice_client
            voice_client.resume()
            return
        #connects bot to voice channel if it's not in there
        if not ctx.voice_client:
            voice_channel = ctx.author.voice.channel
            voice_client = await voice_channel.connect()
            url = download_audio(yt_url)
            audio_source = FFmpegPCMAudio(url)
            voice_client.play(audio_source, after=lambda e: play_next(ctx))
        else:
            url = download_audio(yt_url)
            yt_queue.append(url)
            await ctx.send("Your song has been added to the queue.")
            await ctx.send(f"There are {len(yt_queue)} songs ahead in the queue.")
    except Exception as e:
        print(f"Error: {e}")
        await ctx.send("Please check to make sure url was input correctly.")

@client.command()
async def purgelist(ctx, arg: str, channel_name: str):

    #checks to see if channel exists
    channel = discord.utils.get(ctx.guild.channels, name=channel_name)
    if channel is None:
        await ctx.send(f"channel '{channel_name}' does not exist.")
        return

    #adds or removes channel from the purge list
    if arg == "add":
        if channel.id not in purge_list:
            purge_list.append(channel.id)
            save_purge_list(purge_list)
            await ctx.send(f"Channel '{channel_name}' has been added to the purge list.")
        else: 
            await ctx.send(f"Channel '{channel_name}' is already on the purge list.")
    elif arg == "remove":
        if channel.id in purge_list:
            purge_list.remove(channel.id)
            save_purge_list(purge_list)
            await ctx.send(f"Channel '{channel_name}' has been removed from purge list.")
        else:
            await ctx.send(f"Channel '{channel_name}' is not on the purge list.")

#checks queued up songs
@client.command()
async def queue(ctx):
    if yt_queue_title_names.empty():
        await ctx.send("There is no queue")
        return
    
    await ctx.send(yt_queue_title_names)

#die roll (change to format xdy where x is the number of y sided dice)
@client.command()
async def roll(ctx, arg: int):
    try:
        result = randint(1, int(arg))
        await ctx.send(result)
    except ValueError:
        await ctx.send(f'\"{arg}\" isn\'t a number')

#skips current song
@client.command()
async def skip(ctx):
    if not ctx.voice_client.is_playing():
        await ctx.send("There's no songs in the queue.")
    else:
        ctx.voice_client.stop()
        await ctx.send("Song has been skipped.")

client.run(BOT_TOKEN, log_handler=handler)