import settings

import discord
from discord.ext import commands


logger = settings.logging.getLogger("bot")

def run():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        logger.info(f"User: {bot.user} (ID: {bot.user.id})")

    @bot.command()
    # @commands.has_permissions(manage_messages=True)
    async def ping(ctx):
        await ctx.send('pong')

    
    @bot.command()
    async def helpme(ctx):
        await ctx.send('Help yourself you lazy shit')


    @bot.event
    async def on_message(message):
        if message.reference and message.content.startswith('!quote'):
            # Check if the message is a reply and starts with the command prefix
            replied_message = await message.channel.fetch_message(message.reference.message_id)
            await message.channel.send(f"Original Message: {replied_message.content}")
        else:
            message.channel.send("Reply to a message to quote.")

        await bot.process_commands(message)

    @bot.command()
    async def quote(ctx):
        await ctx.send("Quoted.")

    bot.run(settings.DISCORD_API_SECRET, root_logger=True)
    # print(settings.DISCORD_API_SECRET)


if __name__ == '__main__':
    run()