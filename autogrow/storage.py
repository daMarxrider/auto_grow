import sqlite3
import time

from .vpd import vpd_kpa


class Storage:
    def __init__(self, path="autogrow.db"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS readings"
            "(ts REAL PRIMARY KEY, temp REAL, rh REAL, vpd REAL)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS actions(ts REAL, fan REAL, lamp REAL, reason TEXT)"
        )

    def log_action(self, fan, lamp, reason):
        self.db.execute("INSERT INTO actions VALUES (?,?,?,?)", (time.time(), fan, lamp, reason))
        self.db.commit()

    def add(self, temp, rh, ts=None):
        self.db.execute(
            "INSERT INTO readings VALUES (?,?,?,?)",
            (ts or time.time(), temp, rh, vpd_kpa(temp, rh)),
        )
        self.db.commit()

    def since(self, seconds):
        cur = self.db.execute(
            "SELECT ts,temp,rh,vpd FROM readings WHERE ts>=? ORDER BY ts",
            (time.time() - seconds,),
        )
        return [dict(zip(("ts", "temp", "rh", "vpd"), r)) for r in cur]
