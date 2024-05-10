import settings

import os
import asyncio

# discord imports
import discord
from discord.ext import commands

# sqlite imports
import aiosqlite

# music api imports
import pafy
import youtube_dl


voice_clients = {}

yt_dl_opts = {'format': 'bestaudio/best'}
ytdl = youtube_dl.YoutubeDL(yt_dl_opts)

ffmpeg_options = {'options': '-vn'}



logger = settings.logging.getLogger("bot")

def run():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        logger.info(f"User: {bot.user} (ID: {bot.user.id})")

        # db connection
        async with aiosqlite.connect("main.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, guild INTEGER, username VARCHAR(255))')
            await db.commit()

            async with db.cursor() as cursor:
                await cursor.execute('CREATE TABLE IF NOT EXISTS quotes (id INTEGER PRIMARY KEY AUTOINCREMENT, guild INTEGER, content VARCHAR(500), author VARCHAR(255))')
            await db.commit()

    @bot.command()
    async def ping(ctx):
        await ctx.send('pong')

    
    @bot.command()
    async def helpme(ctx):

        all_commands = {
            "!ping": "replies with pong",
            "!helpme": "this.",
            "!quote": "Reply to a message with this to save the quote.",
            "!get_qoutes": "Gets quotes by member.",
            "!join": "Make Bot join voice chat.",
            "!leave": "Make bot leave voice chat.",
            "!play": "Plays song from linked youtube URL.",
            "!pause": "Pauses the song.",
            "!unpause": "Unpauses the song."
        }

        await ctx.send('Help yourself you lazy shit')


    @bot.command()
    async def adduser(ctx, member:discord.Member):
        async with aiosqlite.connect("main.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute("SELECT id FROM users WHERE guild = ?", (ctx.guild.id,))
                data = await cursor.fetchone()
                if data:
                    await cursor.execute("UPDATE users SET id = ? WHERE guild = ?", (member.id, ctx.guild.id,))
                else:
                    await cursor.execute("INSERT INTO users (id, guild, username) VALUES (?, ?, ?)", (member.id, ctx.guild.id, member.name,))
            await db.commit()

    @bot.event
    async def on_message(message):

        if message.author == bot.user:
            return  # Ignore messages sent by the bot itself

        if message.reference and message.content.startswith('!quote'):
            # Check if the message is a reply and starts with the command prefix
            replied_message = await message.channel.fetch_message(message.reference.message_id)
            # await message.channel.send(f"Original Message: {replied_message.content}")
            
            # save to database
            async with aiosqlite.connect("main.db") as db:
                async with db.cursor() as cursor:
                    await cursor.execute("INSERT INTO quotes (guild, content, author) VALUES (?, ?,  ?)",
                                         (message.guild.id, replied_message.content, replied_message.author.name,))
                await db.commit()
            
            # debug messages
            print(replied_message.id)
            print("Quoted Text: " + replied_message.content)
            print(replied_message.author)
            
            # else command is not working
        elif message.content.startswith('!quote'):
            await message.channel.send("Reply to a message to quote.")

        await bot.process_commands(message)

    @bot.command()
    async def quote(ctx):
        await ctx.send("Quoted.")


    # needs changes to give niced error handling
    # @bot.command()
    # async def join(ctx):
    #     channel = ctx.author.voice.channel
    #     await channel.connect()


    # disconnect / leave
    @bot.command()
    async def stop(ctx):
        await ctx.voice_client.disconnect()


    # play command
    @bot.command()
    async def play(ctx, video_url):

        # function needs to include !join
        voice_channel = ctx.author.voice.channel
        await voice_channel.connect()

        # function needs to include automatic queueing
        voice_client = ctx.voice_client
        
        # if voice_client.is_playing():
        #     await ctx.send("Already playing a song")
        #     return

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(video_url, download=False))

        song = data['url']
        player = discord.FFmpegPCMAudio(song, **ffmpeg_options)
        voice_client.play(player)

        del data


    # pause
    @bot.command()
    async def pause(ctx):
        voice_channel = ctx.author.voice.channel
        voice_client = ctx.voice_client

        if voice_client is None:
            await voice_channel.connect()
            voice_client = ctx.voice_client

        if voice_client.is_playing():
            voice_client.pause()
        else:
            await ctx.send("Play smth to pause")


    # resume
    @bot.command()
    async def unpause(ctx):
        voice_channel = ctx.author.voice.channel
        voice_client = ctx.voice_client

        if voice_client is None:
            await voice_channel.connect()
            voice_client = ctx.voice_client

        if voice_client.is_playing() == False:
            voice_client.resume()
        else:
            await ctx.send("Nothing was playing.")

    # needs some discord message styling so that its not just plain text
    @bot.command() # add catch for if member does not exist --> member error ON function call
    async def get_quotes(ctx, member:discord.Member):
        async with aiosqlite.connect("main.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute("SELECT * FROM quotes WHERE author = ?", (member.name,))
                data = await cursor.fetchall()
                if data:
                    for quote in data:
                        # print(str(quote.content) + " : " + str(quote.author))
                        await ctx.send("> **" + quote[2] + "** : *" + quote[3] + "*")
                else:
                    await ctx.send("no quotes by " + str(member.name))
            await db.commit()
        

    bot.run(settings.DISCORD_API_SECRET, root_logger=True)


if __name__ == '__main__':
    run()