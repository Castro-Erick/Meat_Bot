import asyncio
import discord
import logging
import youtube_dl

from discord.ext import commands
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

#displays message on launch when bot is ready
@client.event
async def on_ready():
    print("MeatBot reporting for duty!")
    print("---------------------")

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

#checks queued up songs
@client.command()
async def queue(ctx):
    if yt_queue_title_names.empty():
        await ctx.send("There is no queue")
        return
    
    await ctx.send(yt_queue_title_names)

#die roll (change to format xdy where x is the number of y sided dice)
@client.command()
async def roll(ctx, arg):
    try:
        result = randint(1, int(arg))
        await ctx.send(result)
    except:
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