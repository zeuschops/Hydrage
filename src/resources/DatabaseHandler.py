from datetime import datetime
import sqlite3 as sqlite
from enum import Enum
import os

class DatabaseEventType(Enum):
    guild_joined = 1
    guild_left = 2
    voice_channel_joined = 3
    voice_channel_left = 4
    received_private_message = 5
    sent_private_message = 6
    received_text_channel_command = 7
    responded_to_text_channel_command = 8
    enabled_logging_in_guild = 9
    bot_started = 10
    message_received = 11
    message_sent = 12
    message_deleted = 13
    message_edited = 14
    guild_updated = 15
    channel_updated = 16
    member_joined = 17
    member_left = 18
    member_updated = 19
    member_banned = 20


#TODO: Dynamically fetch which column to be pulling to be certain what field to respond later
class DatabaseHandler:
    def __init__(self, file:str):
        if file not in os.listdir('./'):
            #TODO: Build base files for tests later...
            pass
        self.sql = sqlite.connect(file)
        self.cur = self.sql.cursor()
    
    def convert_data_to_dict(headers:list[str], data:list[list[str]]):
        if len(headers) == len(data[0]):
            to_return = []
            for i in range(len(data)):
                to_return.append({})
                for j in range(len(headers)):
                    to_return[-1].update({headers[j]:data[i][j]})
            return to_return

    def get_token(self, service:str) -> str:
        self.cur.execute("SELECT token FROM tokens WHERE service_name=\"%s\"" % service)
        resp = self.cur.fetchone()
        return resp[0]
    
    def get_owner(self) -> dict:
        self.cur.execute("SELECT * FROM owner")
        headers = [i[0] for i in self.cur.description]
        resp = self.cur.fetchone()
        to_return = {}
        if len(resp) == len(headers):
            for i in range(len(resp)):
                to_return.update({headers[i]:resp[i]})
        return to_return
    
    def is_guild_logging(self, guild_id:str) -> bool:
        self.cur.execute("SELECT * FROM event_view WHERE name=\"enabled logging in guild\" AND guild_id=\"%s\"" % guild_id)
        resp = self.cur.fetchone()
        return len(resp) > 0
    
    def get_guild_logging_channel(self, guild_id:str):
        self.cur.execute("SELECT * FROM event_view WHERE name=\"enabled logging in guild\" AND guild_id=\"%s\" ORDER BY date DESC" % guild_id)
        resp = self.cur.fetchone()
        if len(resp) > 0:
            return resp[2]
        return None
    
    def set_guild_logging_channel(self, guild_id:str, channel_id:str, date:datetime):
        self.cur.execute("SELECT * FROM event_history")
        headers = [i[0] for i in self.cur.description]
        self.cur.execute("INSERT INTO event_history(id, event_type, guild_id, channel_id, is_voice_channel, is_private_message, date) VALUES ((SELECT count(*)+1 FROM event_history), %i, \"%s\", \"%s\", False, False, \"%s\")" % (DatabaseEventType.enabled_logging_in_guild.value, guild_id, channel_id, date.strftime("%Y-%m-%d %H:%M:%S")))

    def add_server(self, id:str, owner_id:str, splash_url:str, banner_url:str, icon_url:str):
        self.cur.execute("INSERT INTO server_info(id, owner_id, splash, banner, icon) VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\");" % (id, owner_id, splash_url, banner_url, icon_url))
        self.sql.commit()
        self.cur = self.sql.cursor()
    
    def add_channel(self, id:str, server_info:str, name:str, position:int, created_at:datetime):
        self.cur.execute("INSERT INTO channel_info(id, server_info, name, position, created_at) VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")" % (id, server_info, name, position, created_at.strftime("%Y-%m-%d %H:%M:%S")))
        self.sql.commit()
        self.cur = self.sql.cursor()
    
    def new_event(self, event_type:DatabaseEventType, guild_id:str, channel_id:str, is_voice_channel:bool, is_private_message:bool, date:datetime):
        self.cur.execute("SELECT * FROM event_history")
        headers = self.cur.description
        self.cur.execute("INSERT INTO event_history(id, event_type, guild_id, channel_id, is_voice_channel, is_private_message, date) VALUES ((SELECT count(*)+1 FROM event_history), %i, \"%s\",\"%s\",\"%s\",\"%s\",\"%s\")" % (event_type.value, guild_id, channel_id, is_voice_channel, is_private_message, date.strftime("%Y-%m-%d %H:%M:%S")))
        self.sql.commit()
        self.cur = self.sql.cursor()
    
    def new_message(self, id:str, server_id:str, channel_id:str, author_id:str, created_at:datetime, mcontent:str):
        self.cur.execute("INSERT INTO messages(id, guild_id, channel_id, author_id, created_at, content) VALUES (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (id, server_id, channel_id, author_id, created_at.strftime("%Y-%m-%d %H:%M:%S"), mcontent))
        self.sql.commit()
        self.cur = self.sql.cursor()

    def message_edit(self, id:str, new_content:str, edited_at:datetime):
        self.cur.execute("SELECT * FROM messages WHERE id=\"%s\"" % id)
        msg = self.cur.fetchone()
        self.cur.execute("INSERT INTO messages(id, guild_id, author_id, created_at, edited_at, content) VALUES (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\");" % (id, msg[1], msg[3], msg[4], edited_at.strftime("%Y-%m-%d %H:%M:%S"), new_content))
        self.cur.execute("INSERT INTO event_history(id, event_type, guild_id, channel_id, is_voice_channel, is_private_message, date) VALUES (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\");" % (id, DatabaseEventType.message_edited, msg[1], msg[2], False, False, edited_at.strftime("%Y-%m-%d %H:%M:%S")))
        self.sql.commit()
        self.cur = self.sql.cursor()
    
    def get_message(self, id:str, guild_id:str):
        self.cur.execute("SELECT * FROM messages WHERE id=\"%s\" AND guild_id=\"%s\"" % (id, guild_id))
        headers = [description[0] for description in self.cur.description] #Get headers to return dict for ease-of-use when/if responses update
        response = self.cur.fetchone()
        to_return = {}
        for i in range(len(headers)):
            to_return.update({headers[i]: response[i]})
        return to_return
    
    def delete_message(self, id:str, guild_id:str):
        self.cur.execute("DELETE FROM messages WHERE id=\"%s\" AND guild_id=\"%s\"" % (id, guild_id))
        self.sql.commit()
        self.cur = self.sql.cursor()
