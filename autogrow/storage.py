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
        self.db.execute("CREATE TABLE IF NOT EXISTS soil(ts REAL, moisture REAL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS waterings(ts REAL, ml REAL, reason TEXT)")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS actions(ts REAL, fan REAL, lamp REAL, reason TEXT)"
        )

    def add_soil(self, moisture):
        self.db.execute("INSERT INTO soil VALUES (?,?)", (time.time(), moisture))
        self.db.commit()

    def last_soil(self):
        r = self.db.execute("SELECT moisture FROM soil ORDER BY ts DESC LIMIT 1").fetchone()
        return r[0] if r else None

    def log_water(self, ml, reason, ts=None):
        self.db.execute("INSERT INTO waterings VALUES (?,?,?)", (ts or time.time(), ml, reason))
        self.db.commit()

    def water_ml_since(self, seconds, now=None):
        r = self.db.execute(
            "SELECT COALESCE(SUM(ml),0) FROM waterings WHERE ts>=?", ((now or time.time()) - seconds,)
        ).fetchone()
        return r[0]

    def last_water_ts(self):
        r = self.db.execute("SELECT MAX(ts) FROM waterings WHERE ml>0").fetchone()
        return r[0]

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
