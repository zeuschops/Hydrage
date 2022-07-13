import os
import json
import asyncio
import requests
import argparse
from datetime import datetime
import discord
from discord.ext import commands

from commands.Music import Music
from commands.Administrator import Administrator
from commands.RiotGamesAPI import RiotGamesAPI
from resources.DatabaseHandler import DatabaseHandler
from resources.DatabaseHandler import DatabaseEventType

argpar = argparse.ArgumentParser(prefix_chars="-")
argpar.add_argument("-debug", action="store_true")
args = argpar.parse_args()


intents = discord.Intents.default()
intents.members = True
intents.messages = True

string_time = "%d-%m-%Y %H:%M:%S"
prefix = 'h!' if not args.debug else 'hb!'
bot = commands.Bot(command_prefix=prefix, intents=intents)
bot.remove_command('help')
dbh = DatabaseHandler("database.sqlite")

@bot.event
async def on_ready():
    bot.add_cog(Music(bot))
    bot.add_cog(Administrator(bot, dbh))
    bot.add_cog(RiotGamesAPI(bot, dbh.get_token('riot-games')))
    print("Logged in as {0.user}".format(bot))
    print("\twith client id {0.user.id}".format(bot))

@bot.event
async def on_message(message):
    dbh.new_event(DatabaseEventType.message_received, message.guild.id, message.channel.id, False, False, message.created_at)
    dbh.new_message(message.id, message.guild.id, message.channel.id, message.author.id, message.created_at, message.content)
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    guild_channel = dbh.get_guild_logging_channel(after.guild.id)
    if guild_channel is not None:
        guild_channel = int(guild_channel)
        name = before.author.nick
        if type(name) is type(None):
            name = before.author.name
        name += "#%s" % before.author.discriminator
        embed = discord.Embed(color=discord.Colour.orange())
        embed.add_field(name="Message before edit", value=before.content, inline=False)
        embed.add_field(name="Message after edit", value=after.content, inline=False)
        embed.set_footer(text="%s | %s" % (name, after.edited_at.strftime(string_time)))
        channel = after.guild.get_channel(guild_channel)
        await channel.send('', embed=embed)
        dbh.new_event(DatabaseEventType.message_received, after.guild.id, after.channel.id, False, False, after.edited_at)
        dbh.message_edit(after.id, after.content, after.edited_at)

@bot.event
async def on_message_delete(message):
    guild_channel = dbh.get_guild_logging_channel(message.guild.id)
    if guild_channel is not None:
        guild_channel = int(guild_channel)
        name = message.author.nick
        if type(name) is type(None):
            name = message.author.name
        name += "#%s" % message.author.discriminator
        embed = discord.Embed(color=discord.Colour.red())
        embed.add_field(name="Deleted Message", value=message.content, inline=False)
        embed.add_field(name="Message ID", value=message.id, inline=False)
        embed.add_field(name="Channel", value=message.channel.mention)
        avatar = message.author.avatar_url
        embed.set_footer(text="%s | %s" % (name, datetime.now().strftime(string_time)), icon_url=avatar)
        channel = message.guild.get_channel(int(guild_channel))
        await channel.send('', embed=embed)
        dbh.new_event(DatabaseEventType.message_deleted, message.guild.id, message.channel.id, False, False, datetime.now())
    
@bot.event
async def on_raw_message_delete(payload):
    guild_channel = dbh.get_guild_logging_channel(str(payload.guild_id))
    if guild_channel is not None:
        guild_channel = int(guild_channel)
        msg = dbh.get_message(str(payload.message_id), str(payload.guild_id))
        await asyncio.sleep(3)
        last_message = None
        async for message in bot.get_channel(guild_channel).history(limit=10):
            if message.author == bot.user:
                if len(message.embeds) == 1:
                    if len(message.embeds[0].fields) >= 2:
                        for i in range(len(message.embeds[0].fields)):
                            if "Message ID" in message.embeds[0].fields[i].name:
                                if str(message.embeds[0].fields[i].value) in str(payload.message_id):
                                    last_message = message
        if type(last_message) is type(None):
            if type(msg) is not type(None):
                embed = discord.Embed(color=discord.Colour.red(), title="Message deleted")
                embed.add_field(name="Message content", value="%s" % msg["content"])
                user = bot.get_user(msg['author_id'])
                if type(user) is type(None):
                    user = bot.get_guild(payload.guild_id).get_member(msg['author_id'])
                if type(user) is not type(None):
                    embed.set_footer(text="Author - %s#%s" % (user.name, str(user.discriminator)), icon_url=user.avatar_url)
                else:
                    embed.set_footer(text='Author ID: %s' % msg['author_id'])
                channel = bot.get_channel(guild_channel)
                await channel.send('', embed=embed)
            else:
                embed = discord.Embed(color=discord.Colour.red(), title="Old message deleted")
                embed.add_field(name="Deleted Message", value="ID: %s" % payload.message_id)
                embed.add_field(name="Deleted in Channel", value="ID: %s" % payload.channel_id)
                channel = bot.get_channel(guild_channel)
                await channel.send('', embed=embed)
            dbh.new_event(DatabaseEventType.message_deleted, payload.message_id, payload.channel_id, False, False, datetime.now())
        dbh.delete_message(payload.message_id, payload.guild_id)

@bot.event
async def on_member_join(member):
    guild_channel = dbh.get_guild_logging_channel(member.guild.id)
    if guild_channel is not None:
        guild_channel = int(guild_channel)
        name = member.nick
        if type(name) is type(None):
            name = member.name
        name += "#%s" % member.discriminator
        embed = discord.Embed(color=discord.Colour.green(), title="User joined")
        embed.set_footer(text="%s | %s" % (name, member.joined_at.strftime(string_time)))
        channel = member.guild.get_channel(guild_channel)
        await channel.send('', embed=embed)
        dbh.new_event(DatabaseEventType.member_joined, member.guild.id, "", False, False, member.joined_at)

@bot.event
async def on_member_remove(member):
    guild_channel = dbh.get_guild_logging_channel(member.guild.id)
    if guild_channel is not None:
        guild_channel = int(guild_channel)
        name = member.nick
        if type(name) is type(None):
            name = member.name
        name += "#%s" % member.discriminator
        embed = discord.Embed(color=discord.Colour.red(), title="User left server")
        embed.set_footer(text=name)
        channel = member.guild.get_channel(guild_channel)
        await channel.send('', embed=embed)
        dbh.new_event(DatabaseEventType.member_banned, member.guild.id, "", False, False, datetime.now())

@bot.event
async def on_guild_join(guild):
    dbh.new_event(DatabaseEventType.guild_joined, guild.id, "", False, False, datetime.now())
    dbh.add_server(guild.id, guild.owner_id, guild.splash_url, guild.banner_url, guild.icon_url)

@bot.event
async def on_guild_remove(guild):
    dbh.new_event(DatabaseEventType.guild_left, guild.id, "", False, False, datetime.now())

@bot.command()
async def ping(ctx):
    await ctx.channel.send(str(int(round(bot.latency * 1000,0))) + " ms")

@bot.command()
async def urlcheck(ctx, url:str):
    req = requests.get(url)
    if req.url.lower() in url.lower():
        await ctx.channel.send("Link is not shortened!")
    else:
        await ctx.channel.send("Link is shortened. Source URL is " + req.url)

@bot.command()
async def invite(ctx):
    await ctx.channel.send("Invite me to your server! https://discord.com/oauth2/authorize?client_id=%s&scope=bot&permissions=309668928" % bot.user.id)

@bot.command()
async def github(ctx):
    await ctx.channel.send("Check out the project on GitHub! https://github.com/zeuschops/Hydrage")

@bot.command()
async def update(ctx):
    if ctx.message.author.id == 454598334448009216:
        try:
            await ctx.message.delete()
        except:
            await ctx.send("Cannot delete messages..", delete_after=5)
            await asyncio.sleep(5)
        await bot.close()

@bot.command()
async def help(ctx, *input):
    commands = {
        "clean": {
            "description":"Clears a given number of messages within a channel",
            "usage": prefix + "clean <numberOfMessages:int>"
        },
        
    }

    user = ctx.message.author
    embed = discord.Embed(color=discord.Color.blue())
    if type(user) is discord.Member:
        if user.guild_permissions.administrator:
            embed.color = discord.Color.red()
            embed.add_field(name='clean', value='Clears a given number of messages within the server', inline=False)
            embed.add_field(name='setLog', value='Sets the logging channel for the server', inline=False)
        if user.guild_permissions.manage_messages and not user.guild_permissions.administrator:
            embed.add_field(name='clean', value='Clears a given number of messages within the server', inline=False)
        if user.guild_permissions.connect or user.guild_permissions.administrator:
            embed.add_field(name='join', value='Forces the bot to connect to your current music channel', inline=False)
            embed.add_field(name='play', value='Plays a song from a YouTube, Vimeo, etc link, or searches for the song', inline=False)
            embed.add_field(name='now', value='Displays currently playing music', inline=False)
            embed.add_field(name='skip', value='Skips currently playing song', inline=False)
            embed.add_field(name='stop', value='Stops playing all music in the queue, and clears the queue', inline=False)
            embed.add_field(name='pause', value='Pauses currently playing song', inline=False)
            embed.add_field(name='resume', value='Resumes the current song in the queue', inline=False)
            embed.add_field(name='queue', value='Displays currently available songs', inline=False)
            embed.add_field(name='shuffle', value='Shuffles current queue', inline=False)
    if user.id == 454598334448009216:
        embed.color = discord.Color.gold()
        embed.add_field(name='update', value='Updates bot to latest main branch')
    #Else: only add default commands that everyone can use with the bot (not all commands available, mind you!)
    embed.add_field(name='summoner', value='Pulls summoner information for League of Legends', inline=False)
    embed.add_field(name='champion', value='Gets the free champion rotation for the week in League of Legends', inline=False)
    embed.add_field(name='recentMatch', value='Gets the most recent match for a given summoner in League of Legends in a suggested region', inline=False)
    embed.add_field(name='matchforid', value='Gets a match in a specified region with a particular matchId from League of Legends', inline=False)
    embed.add_field(name='riotregions', value='Displays all available regions to request data from Riot Games for League of Legends', inline=False)
    embed.add_field(name='ping', value='Checks latency of the bot in milliseconds', inline=False)
    embed.add_field(name='github', value='Provides a link to contribute to the source code for this bot', inline=False)
    embed.add_field(name='urlcheck', value='Checks any URL to confirm that the URL is not shortened, and provides which URL this navigates to if it is', inline=False)
    embed.set_footer(text='%s#%s | %s' % (ctx.message.author.name, ctx.message.author.discriminator, ctx.message.created_at.strftime(string_time)))
    await ctx.send('', embed=embed)

if args.debug:
    bot.run(dbh.get_token('discord-beta'), bot=True)
else:
    bot.run(dbh.get_token("discord"), bot=True)
