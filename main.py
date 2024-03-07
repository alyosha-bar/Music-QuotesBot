import settings

import discord
from discord.ext import commands

import aiosqlite

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
            
            async with aiosqlite.connect("main.db") as db:
                async with db.cursor() as cursor:
                    await cursor.execute("INSERT INTO quotes (guild, content, author) VALUES (?, ?,  ?)",
                                         (message.guild.id, replied_message.content, replied_message.author.name,))
                await db.commit()
            # save to database
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


    @bot.command() # add catch for if member does not exist --> member error ON function call
    async def get_quotes(ctx, member:discord.Member):
        async with aiosqlite.connect("main.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute("SELECT * FROM quotes WHERE author = ?", (member.name,))
                data = await cursor.fetchall()
                if data:
                    for quote in data:
                        # print(str(quote.content) + " : " + str(quote.author))
                        await ctx.send(quote[2] + " : " + quote[3])
                else:
                    print("no quotes by " + str(member.name))
            await db.commit()
        

    bot.run(settings.DISCORD_API_SECRET, root_logger=True)
    # print(settings.DISCORD_API_SECRET)


if __name__ == '__main__':
    run()