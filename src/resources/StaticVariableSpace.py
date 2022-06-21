import os
import json

#TODO: Refactor this to utilize SQLite instead

class StaticVariableSpace:
    def __init__(self):
        self.vars = {}
        self.filename = "config.json"

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(StaticVariableSpace, cls).__new__(cls)
        return cls.instance
    
    def set(self, key:str, val):
        self.vars.update({key:val})
    
    def get(self, key:str):
        if key in list(self.vars):
            return self.vars[key]
        else:
            return None
    
    def keys(self):
        return list(self.vars)
    
    def save(self):
        f = open(self.filename,'w')
        f.write(json.dumps(self.vars, indent=4, separators=(',',':')))
        f.close()
    
    def load(self):
        if self.filename in os.listdir('./'):
            f = open(self.filename,'r')
            self.vars = json.loads(f.read())
            f.close()