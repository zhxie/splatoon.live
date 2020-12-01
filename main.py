import os
import sqlite3
from flask import Flask, redirect, abort, g

app = Flask(__name__)

DATABASE = "data.db"


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

        c = db.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users(
            name    TEXT PRIMARY KEY NOT NULL UNIQUE,
            address TEXT NOT NULL
            );''')
    return db


def get_live_addr(name):
    c = get_db().cursor()
    cursor = c.execute(
        "SELECT address FROM users WHERE name = '{}'".format(name))

    if cursor.rowcount == 0:
        return None
    else:
        return cursor.fetchone()[0]


@app.route('/<name>')
def live(name):
    addr = get_live_addr(name)
    if addr == None:
        abort(404)
    else:
        return redirect(addr, code=302)


@app.teardown_appcontext
def close_conn(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
