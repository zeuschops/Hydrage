import os
import json
import asyncio
import requests
from datetime import datetime
import discord
from discord.ext import commands

from commands.Music import Music
from commands.Administrator import Administrator
from resources.DatabaseHandler import DatabaseHandler
from resources.DatabaseHandler import DatabaseEventType

intents = discord.Intents.default()
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix="h!", intents=intents)
dbh = DatabaseHandler("database.sqlite")

@bot.event
async def on_ready():
    bot.add_cog(Music(bot))
    bot.add_cog(Administrator(bot, dbh))
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
        embed.set_author(name=name)
        channel = after.guild.get_channel(guild_channel)
        await channel.send('', embed=embed)
        dbh.new_event(DatabaseEventType.message_received, after.guild.id, after.channel.id, False, False, after.edited_at)
        dbh.message_edit(after.id, after.content, after.edited_at)

@bot.event
async def on_message_delete(message):
    # guild_channel = dbh.get_guild_logging_channel(message.guild.id)
    # if guild_channel is not None:
    #     guild_channel = int(guild_channel)
    #     name = message.author.nick
    #     if type(name) is type(None):
    #         name = message.author.name
    #     name += "#%s" % message.author.discriminator
    #     embed = discord.Embed(color=discord.Colour.red())
    #     embed.add_field(name="Deleted Message", value=message.content, inline=False)
    #     embed.add_field(name="Message ID", value=message.id, inline=False)
    #     embed.set_author(name=name)
    #     channel = message.guild.get_channel(int(guild_channel))
    #     #await channel.send('', embed=embed)
        dbh.new_event(DatabaseEventType.message_deleted, message.guild.id, message.channel.id, False, False, datetime.now())
    
@bot.event
async def on_raw_message_delete(payload):
    guild_channel = dbh.get_guild_logging_channel(str(payload.guild_id))
    if guild_channel is not None:
        guild_channel = int(guild_channel)
        msg = dbh.get_message(str(payload.message_id), str(payload.guild_id))
        if type(msg) is not type(None):
            embed = discord.Embed(color=discord.Colour.red(), title="Message deleted")
            embed.add_field(name="Message content", value="%s" % msg["content"])
            user = bot.get_user(msg['author_id'])
            if type(user) is type(None):
                user = bot.get_guild(payload.guild_id).get_member(msg['author_id'])
            if type(user) is not type(None):
                embed.set_author(name="Author - %s#%s" % (user.name, str(user.discriminator)), icon_url=user.avatar_url)
            else:
                embed.set_author(name='Author ID: ' % msg['author_id'])
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
        embed.set_author(name=name)
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
        embed.set_author(name=name)
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
    await ctx.channel.send(str(int(round(bot.latency * 1000,0))) + " ms", delete_after=15)

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

bot.run(dbh.get_token("discord"), bot=True)
