import os
import sqlite3
from flask import Flask, redirect, abort, g, request, jsonify

app = Flask(__name__)

DATABASE = "data.db"

REGISTER_SUCCESS = 0
REGISTER_FAIL_TOO_SHORT = 1
REGISTER_FAIL_ALIAS_TOO_SHORT = 2
REGISTER_FAIL_EXISTED = 3
REGISTER_FAIL_AUDITING = 4
REGISTER_FAIL_ADDR_EXISTED = 5
REGISTER_FAIL_ALIAS_EXISTED = 6
REGISTER_FAIL_DB = 7


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

        c = db.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users(
            name    TEXT PRIMARY KEY NOT NULL UNIQUE,
            address TEXT NOT NULL,
            alias   TEXT,
            audited INTEGER NOT NULL
            );''')
    return db


def commit_db():
    db = getattr(g, '_database', None)
    try:
        db.commit()
        return True
    except:
        db.rollback()
        return False


def get_addr(name):
    c = get_db().cursor()
    cursor = c.execute(
        "SELECT address FROM users WHERE name = '{}' AND audited = 1".format(name))

    row = cursor.fetchone()
    if row == None:
        cursor = c.execute(
            "SELECT address FROM users WHERE alias = '{}' AND audited = 1".format(name))
        row = cursor.fetchone()

    if row == None:
        return None
    else:
        return row[0]


@ app.route('/r', methods=['POST'])
def register():
    user = request.get_json(silent=True)
    if user == None:
        abort(400)
    else:
        if "name" in user and "address" in user:
            name = user["name"]
            if len(name) < 2:
                return jsonify(status=REGISTER_FAIL_TOO_SHORT)
            address = user["address"]
            alias = None
            if "alias" in user:
                alias = user["alias"]
                if len(alias) < 2:
                    return jsonify(status=REGISTER_FAIL_ALIAS_TOO_SHORT)

            c = get_db().cursor()

            cursor = c.execute(
                "SELECT audited FROM users WHERE name = '{}'".format(name))
            row = cursor.fetchone()
            if row != None:
                if row[0] == 0:
                    return jsonify(status=REGISTER_FAIL_AUDITING)
                else:
                    return jsonify(status=REGISTER_FAIL_EXISTED)

            cursor = c.execute(
                "SELECT audited FROM users WHERE address = '{}'".format(address))
            row = cursor.fetchone()
            if row != None:
                return jsonify(status=REGISTER_FAIL_ADDR_EXISTED)

            if alias != None:
                cursor = c.execute(
                    "SELECT audited FROM users WHERE alias = '{}'".format(alias))
                row = cursor.fetchone()
                if row != None:
                    return jsonify(status=REGISTER_FAIL_ALIAS_EXISTED)

            if alias == None:
                c.execute("INSERT INTO users (name, address, audited) VALUES ('{}', '{}', 0)".format(
                    name, address))
            else:
                c.execute("INSERT INTO users (name, address, alias, audited) VALUES ('{}', '{}', '{}', 0)".format(
                    name, address, alias))

            if commit_db():
                return jsonify(status=REGISTER_SUCCESS)
            else:
                return jsonify(status=REGISTER_FAIL_DB)

            abort(404)
        else:
            abort(400)


@ app.route('/<name>')
def live(name):
    addr = get_addr(name)
    if addr == None:
        abort(404)
    else:
        return redirect(addr, code=302)


@ app.teardown_appcontext
def close_conn(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
