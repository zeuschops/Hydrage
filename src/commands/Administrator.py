import json
import discord
from discord.ext import commands

from resources.StaticVariableSpace import StaticVariableSpace

class Administrator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.svs = StaticVariableSpace()

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
        if 'logging' in self.svs.keys():
            if ctx.guild.id not in self.svs.get('logging'):
                self.svs.get('logging').update({ctx.guild.id:to_channel.id})
                await ctx.channel.send('Set logging channel to %s!' % to_channel.mention)
            else:
                old = self.svs.get('logging')[ctx.guild.id]
                self.svs.get('logging')[ctx.guild.id] = to_channel.id
                await ctx.channel.send('Switch from channel %s to %s!' % (old.mention, to_channel.mention))
        else:
            self.svs.set('logging', {})
            self.svs.get('logging').update({ctx.guild.id:to_channel.id})
        self.svs.save()
