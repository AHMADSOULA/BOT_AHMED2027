import aiosqlite
import os
import datetime
from config import config

os.makedirs(os.path.dirname(config.DB_PATH) or ".", exist_ok=True)

async def init_db():
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                access INTEGER DEFAULT 0,
                banned INTEGER DEFAULT 0,
                priority INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id INTEGER PRIMARY KEY,
                sso_url TEXT,
                state TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        await db.commit()

async def register_user(user_id, username):
    async with aiosqlite.connect(config.DB_PATH) as db:
        access = 1 if user_id == config.ADMIN_ID else 0
        await db.execute("INSERT OR IGNORE INTO users (user_id, username, access) VALUES (?, ?, ?)", (user_id, username, access))
        await db.commit()

async def has_access(user_id):
    if user_id == config.ADMIN_ID: return True
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT access, banned FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return bool(row and row["access"] == 1 and row["banned"] == 0)

async def set_access(user_id, val):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("UPDATE users SET access=? WHERE user_id=?", (val, user_id))
        await db.commit()

async def set_ban(user_id, val):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("UPDATE users SET banned=? WHERE user_id=?", (val, user_id))
        await db.commit()

async def set_priority(user_id, val):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("UPDATE users SET priority=? WHERE user_id=?", (val, user_id))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users")
        return [dict(r) for r in await cur.fetchall()]

async def add_request(user_id, username):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("INSERT INTO requests (user_id, username) VALUES (?, ?)", (user_id, username))
        await db.commit()

async def set_session(user_id, sso_url, state):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO sessions (user_id, sso_url, state) VALUES (?, ?, ?)", (user_id, sso_url, state))
        await db.commit()

# ✅ صلحنا هادي (كانت فيها غلط)
async def get_session(user_id):
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM sessions WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def clear_session(user_id):
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        await db.commit()
