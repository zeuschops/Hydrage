import os
import json
import asyncio
import discord
from discord.ext import commands

#Using discord-py-slash-command from pypi
#from discord_slash import SlashCommand, SlashContext

from commands.Music import Music
from commands.Administrator import Administrator
from resources.StaticVariableSpace import StaticVariableSpace

intents = discord.Intents.default()
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix="h!", intents=intents)
#slash = SlashCommand(bot)

@bot.event
async def on_ready():
    svs = StaticVariableSpace()
    bot.add_cog(Music(bot))
    bot.add_cog(Administrator(bot))
    svs.load()
    print("Logged in as {0.user}".format(bot))
    print("\twith client id {0.user.id}".format(bot))

@bot.event
async def on_message(message):
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    svs = StaticVariableSpace()
    svs.load()
    if str(before.guild.id) in list(svs.get('logging')) and before.channel.id != svs.get('logging')[str(before.guild.id)]:
        name = before.author.nick
        if type(name) is type(None):
            name = before.author.name
        name += "#%s" % before.author.discriminator
        embed = discord.Embed(color=discord.Colour.orange())
        embed.add_field(name="Message before edit", value=before.content, inline=False)
        embed.add_field(name="Message after edit", value=after.content, inline=False)
        embed.set_author(name=name)
        channel = after.guild.get_channel(svs.get('logging')[str(after.guild.id)])
        await channel.send('', embed=embed)

@bot.event
async def on_message_delete(message):
    svs = StaticVariableSpace()
    svs.load()
    if str(message.guild.id) in list(svs.get('logging')) and message.channel.id != svs.get('logging')[str(message.guild.id)]:
        name = message.author.nick
        if type(name) is type(None):
            name = message.author.name
        name += "#%s" % message.author.discriminator
        embed = discord.Embed(color=discord.Colour.red())
        embed.add_field(name="Deleted Message", value=message.content, inline=False)
        embed.add_field(name="Message ID", value=message.id, inline=False)
        embed.set_author(name=name)
        channel = message.guild.get_channel(svs.get('logging')[str(message.guild.id)])
        await channel.send('', embed=embed)
    
@bot.event
async def on_raw_message_delete(payload):
    svs = StaticVariableSpace()
    svs.load()
    if str(payload.guild_id) in list(svs.get('logging')) and payload.channel_id != svs.get('logging')[str(payload.guild_id)]:
        embed = discord.Embed(color=discord.Colour.red(), title="Old message deleted")
        embed.add_field(name="Deleted Message", value="ID: %s" % payload.message_id, inline=False)
        embed.add_field(name="In Channel:", value="ID: %s" % payload.channel_id, inline=False)
        embed.add_field(name="Contents", value="[Message contents unavailable]", inline=False)
        channel = bot.get_channel(svs.get('logging')[str(payload.guild_id)])
        await channel.send('', embed=embed)

@bot.event
async def on_member_join(member):
    svs = StaticVariableSpace()
    svs.load()
    if str(member.guild.id) in list(svs.get('logging')):
        name = member.nick
        if type(name) is type(None):
            name = member.name
        name += "#%s" % member.discriminator
        embed = discord.Embed(color=discord.Colour.green(), title="User joined")
        embed.set_author(name=name)
        channel = member.guild.get_channel(svs.get('logging')[str(member.guild.id)])
        await channel.send('', embed=embed)

@bot.event
async def on_member_remove(member):
    svs = StaticVariableSpace()
    svs.load()
    if str(member.guild.id) in list(svs.get('logging')):
        name = member.nick
        if type(name) is type(None):
            name = member.name
        name += "#%s" % member.discriminator
        embed = discord.Embed(color=discord.Colour.red(), title="User exited guild")
        embed.set_author(name=name)
        channel = member.guild.get_channel(svs.get('logging')[str(member.guild.id)])
        await channel.send('', embed=embed)

@bot.event
async def on_guild_join(guild):
    svs = StaticVariableSpace()
    svs.load()
    if 'guilds' not in svs.keys():
        svs.set('guilds', [guild.id])
    else:
        svs.get('guilds').append(guild.id)

@bot.event
async def on_guild_remove(guild):
    svs = StaticVariableSpace()
    svs.load()
    if 'guilds' not in svs.keys():
        svs.set('guilds', [])
    elif guild.id in svs.get('guilds'):
        del svs.get('guilds')[svs.get('guilds').index(guild.id)]

@bot.command()
async def ping(ctx):
    can_delete = False
    try:
        can_delete = bot.user.permissions_in(ctx.channel).manage_messages
    except:
        print("Probably no user perms established yet, not deleting messages.")
        print("\tMessage ID:", ctx.message.id)
        print("\tGuild ID:", ctx.guild.id)
        print("\tTimestamp:", ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    await ctx.channel.send(str(int(round(bot.latency * 1000,0))) + " ms", delete_after=15 if can_delete else None)
    if can_delete:
        await asyncio.sleep(15)
        await ctx.message.delete()

@bot.command()
async def invite(ctx):
    can_delete = False
    try:
        can_delete = bot.user.permissions_in(ctx.channel).manage_messages
    except:
        print("Probably no user perms established yet, not deleting messages.")
        print("\tMessage ID:", ctx.message.id)
        print("\tGuild ID:", ctx.guild.id)
        print("\tTimestamp:", ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    await ctx.channel.send("Invite me to your server! https://discord.com/oauth2/authorize?client_id=%s&scope=bot&permissions=309668928" % bot.user.id)
    if can_delete:
        await asyncio.sleep(10)
        await ctx.message.delete()

#TODO: Refactor this to utilize SQLite more... (I would like to combine this all into 1 file I can .gitignore)
f = open('token.json','r')
config = json.loads(f.read())
f.close()

bot.run(config['token'], bot=True)
