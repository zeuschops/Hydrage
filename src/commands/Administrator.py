import json
from datetime import datetime
import discord
from discord.ext import commands

from resources.DatabaseHandler import DatabaseHandler

class Administrator(commands.Cog):
    def __init__(self, bot, dbh:DatabaseHandler):
        self.bot = bot
        self.dbh = dbh

    @commands.command()
    async def clean(self, ctx, count:int):
        user_perms = ctx.message.author.permissions_in(ctx.channel)
        if user_perms.administrator or user_perms.manage_messages:
            await ctx.channel.purge(limit=count+1) #+1 to account for the message telling the bot to delete messages
            await ctx.send("Deleted " + str(count) + " messages", delete_after=10)
        else:
            await ctx.send("You do not have permission to use this command.", timeout=15)
    
    #TODO: Build out settings command, build configurations for message logging, kicks, bans, timeouts, mutes, channel bans, shadow bans, etc
    # @commands.command()
    # async def settings(self, ctx, option:str, new_settings:str):
    #   

    @commands.command()
    async def setLog(self, ctx, to_channel:discord.TextChannel):
        is_admin = ctx.message.author.guild_permissions.administrator
        if is_admin:
            self.dbh.set_guild_logging_channel(to_channel.guild.id, to_channel.id, datetime.now())
            await ctx.send("Set logging channel to %s" % to_channel.mention)
        else:
            await ctx.send("You do not have the correct permissions to do that! Please contact your server admin (%s) to have that action completed." % ctx.guild.owner.mention)
