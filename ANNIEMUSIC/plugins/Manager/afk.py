from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.types import Message
from ANNIEMUSIC import app
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os

# -------------------------------
# MongoDB Setup
# -------------------------------
MONGO_URL = os.getenv(
    "MONGO_DB_URL",
    "mongodb+srv://rajkhilchi786:lt10XABVqfQqOT1f@cluster0.bug4pqt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo["ANNIEMUSIC"]
afk_collection = db["afk_users"]

# -------------------------------
# /afk Command
# -------------------------------
@app.on_message(filters.command("afk") & ~filters.bot)
async def set_afk(_, message: Message):
    user = message.from_user
    if not user:
        return

    reason = " ".join(message.command[1:]) if len(message.command) > 1 else "No reason provided"
    await afk_collection.update_one(
        {"user_id": user.id},
        {"$set": {"reason": reason, "time": datetime.utcnow(), "name": user.first_name}},
        upsert=True
    )

    await message.reply_text(
        f"😴 {user.mention} is now AFK!\n\n"
        f"🕒 Reason: {reason}\n"
        f"💤 I'll let others know you're away."
    )

# -------------------------------
# Mention / Reply AFK User
# -------------------------------
@app.on_message(filters.text & ~filters.bot, group=5)
async def mention_afk(_, message: Message):
    mentioned_ids = set()

    # 1️⃣ If user replied to someone
    if message.reply_to_message and message.reply_to_message.from_user:
        mentioned_ids.add(message.reply_to_message.from_user.id)

    # 2️⃣ Detect @username or inline mention
    if message.entities:
        for entity in message.entities:
            if entity.type.name == "MENTION":
                username = message.text[entity.offset + 1 : entity.offset + entity.length]
                try:
                    user = await app.get_users(username)
                    mentioned_ids.add(user.id)
                except Exception:
                    pass
            elif entity.type.name == "TEXT_MENTION" and entity.user:
                mentioned_ids.add(entity.user.id)

    # 3️⃣ Check for AFK users
    for user_id in mentioned_ids:
        afk_user = await afk_collection.find_one({"user_id": user_id})
        if afk_user:
            since = datetime.utcnow() - afk_user["time"]
            time_afk = str(timedelta(seconds=int(since.total_seconds())))
            try:
                await message.reply_text(
                    f"💤 [{afk_user['name']}](tg://user?id={user_id}) is currently AFK.\n"
                    f"🕒 Since: {time_afk} ago\n"
                    f"📄 Reason: {afk_user['reason']}"
                )
            except Exception:
                pass

# -------------------------------
# Remove AFK when user speaks
# -------------------------------
@app.on_message(filters.text & ~filters.bot & ~filters.command("afk"), group=6)
async def remove_afk(_, message: Message):
    user = message.from_user
    if not user:
        return

    afk_user = await afk_collection.find_one({"user_id": user.id})
    if afk_user:
        since = datetime.utcnow() - afk_user["time"]
        time_afk = str(timedelta(seconds=int(since.total_seconds())))
        await afk_collection.delete_one({"user_id": user.id})

        await message.reply_text(
            f"✅ Welcome back [{afk_user['name']}](tg://user?id={user.id})!\n"
            f"🕒 You were away for: {time_afk}\n"
            f"📄 Reason: {afk_user['reason']}"
        )

print("✅ afk.py successfully loaded (mention + reply 100% working)")
