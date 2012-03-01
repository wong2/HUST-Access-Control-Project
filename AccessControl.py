#-*-coding:utf-8-*-
import hashlib
from datetime import datetime
import sqlite3 as sqlite

class AccessControl:
    
    def __init__(self, username, pwd):
        pwd = hashlib.md5(pwd).hexdigest()

class AutoAccessControl:   
    
    def __init__(self):
        self.con = sqlite.connect("db.db")
        self.buffer = {}
        READ, WRITE, DELETE, EXECUTE, OWN, CONTROL = range(6)
    
    def determine(self, s_id, f_id, access):
        k = str(s_id) + str(f_id) + str(access)
        if k in self.buffer:
            return self.buffer[k]
        else:
            res = self.con.execute("select id from authorize where subject=? and \
                object=? and access=?", (s_id, f_id, access)).fetchone()
            result = (res!=None)
            self.buffer[k] = result
            return result

def isValidUser(name, pwd):
    con = sqlite.connect("db.db")
    res = con.execute("select id,is_admin from subject where name=? and pwd=?",
        (name, hashlib.md5(pwd).hexdigest())).fetchone()
    con.close()
    if res == None:
        return (None, None)
    else:
        return (res[0], int(res[1]=='Y'))

