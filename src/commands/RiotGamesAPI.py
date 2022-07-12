import requests
from datetime import datetime

import discord
from discord.ext import commands

#TODO: Refactor this to utilize Cecilia

class RiotGamesAPI(commands.Cog):
    def __init__(self, bot, token:str):
        self.bot = bot
        self.headers = {'X-Riot-Token': token}
        self.endpoints = {
            'na':'https://na1.api.riotgames.com',
            'euw':'https://euw1.api.riotgames.com',
            'eun':'https://eun1.api.riotgames.com',
            'br':'https://br1.api.riotgames.com',
            'jp':'https://jp1.api.riotgames.com',
            'kr':'https://kr.api.riotgames.com',
            'la1':'https://la1.api.riotgames.com',
            'la2':'https://la2.api.riotgames.com',
            'oc':'https://oc1.api.riotgames.com',
            'tr':'https://tr1.api.riotgames.com',
            'ru':'https://ru.api.riotgames.com',
            'americas':'https://americas.api.riotgames.com',
            'asia':'https://asia.api.riotgames.com',
            'europe':'https://europe.api.riotgames.com'
        }
    
    @commands.command()
    async def summoner(self, ctx, region:str, summoner:str):
        resp = requests.get(self.endpoints[region.lower()] + '/lol/summoner/v4/summoners/by-name/' + summoner, headers=self.headers)
        if resp.status_code == 200:
            resp_j = resp.json()
            embed = discord.Embed(title=resp_j['name'], url='https://matchhistory.na.leagueoflegends.com/en/#match-history/NA1/230089557')
            embed.add_field(name='id', value=resp_j['id'])
            embed.add_field(name='accountId', value=resp_j['accountId'])
            embed.add_field(name='puuid', value=resp_j['puuid'])
            embed.add_field(name='revisionDate', value=resp_j['revisionDate'])
            embed.add_field(name='summonerLevel', value=resp_j['summonerLevel'])
            embed.set_thumbnail(url='http://ddragon.leagueoflegends.com/cdn/11.7.1/img/profileicon/' + str(resp_j['profileIconId']) + '.png')
            await ctx.send(embed=embed)
        else:
            await ctx.send("Error occurred trying to send request to Riot's API. (HTTP Err %s)" % str(resp.status_code))
    
    @commands.command()
    async def champion(self, ctx, region:str):
        resp = requests.get(self.endpoints[region.lower()] + '/lol/platform/v3/champion-rotations', headers=self.headers)
        if resp.status_code == 200:
            resp_j = resp.json()
            embed = discord.Embed(title="Free Champion Rotations This week")
            embed.add_field(name='Free champions', value=resp_j['freeChampionIds'])
            embed.add_field(name='Free champions for New Players', value=resp_j['freeChampionIdsForNewPlayers'])
            await ctx.send(embed=embed)
        else:
            await ctx.send("Error occurred trying to send request to Riot's API. (HTTP Err %s)" % str(resp.status_code))
        
    @commands.command()
    async def recentMatch(self, ctx, region:str, summoner:str):
        resp = requests.get(self.endpoints[region.lower()] + '/lol/summoner/v4/summoners/by-name/%s' % summoner, headers=self.headers)
        if resp.status_code == 200:
            #puuid = resp['puuid'] #User this with match-v5
            account_id = resp['accountId']
            resp = requests.get(self.endpoints[region.lower()] + '/lol/match/v4/matchlists/by-account/' + account_id, headers=self.headers)
            if resp.status_code == 200:
                resp_j = resp.json()
                match = resp_j['matches'][0]
                embed = discord.Embed(title="Recent match for " + summoner)
                embed.add_field(name='Game ID', value=match['gameId'])
                embed.add_field(name='Champion ID', value=match['champion'])
                embed.add_field(name='timestamp', value=datetime.datetime.fromtimestamp(match['timestamp']/1000).strftime("%Y-%m-%d %H:%M:%S"))
                embed.add_field(name='season', value=match['season'])
                embed.add_field(name='role', value=match['role'])
                embed.add_field(name='lane', value=match['lane'])
                await ctx.send(embed=embed)
                return
        await ctx.send("Issue reaching endpoint. (HTTP Error %s)" % str(resp.status_code))
    
    @commands.command()
    async def matchforid(self, ctx, region:str, matchId:str):
        resp = requests.get(self.endpoints[region.lower()] + '/lol/match/v4/matches/' + matchId, headers=self.headers)
        if resp.status_code == 200:
            resp_j = resp.json()
            red_team = []
            blue_team = []
            for i in resp_j['participantIdentities']:
                name = i['player']['summonerName']
                if i['participantId'] < 6:
                    red_team.append(name)
                else:
                    blue_team.append(name)

            embed = discord.Embed(title="Match for ID - " + matchId)
            embed.add_field(name='Red Team', value='\n'.join(red_team))
            embed.add_field(name='Blue Team', value='\n'.join(blue_team))
            await ctx.send(embed=embed)

    @commands.command()
    async def riotregions(self, ctx):
        await ctx.send('Available regions are ' + str(list(self.endpoints)))
