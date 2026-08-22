from pyrogram import filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ChatType, MessageEntityType
from ANNIEMUSIC import app
from ANNIEMUSIC.utils.decorators.language import language
import asyncio
import json
import os
import atexit
from datetime import datetime

# ------------------------------
# 🔒 BASIC CONFIG
# ------------------------------

LOCK_DATA_FILE = "lock_data.json"

# All available lock types
LOCKABLES = [
    "all", "audio", "bots", "button", "contact", "document",
    "egame", "forward", "game", "gif", "info", "inline",
    "invite", "location", "media", "messages", "other",
    "photo", "pin", "poll", "previews", "rtl", "sticker",
    "url", "username", "video", "voice", "text"
]

# Stylish Emoji for each lock type
EMOJI = {
    "all": "🔐", "audio": "🎵", "bots": "🤖", "button": "🔘", "contact": "📇",
    "document": "📄", "egame": "🎮", "forward": "🔄", "game": "🕹️",
    "gif": "🎞️", "info": "ℹ️", "inline": "⚡", "invite": "🔗",
    "location": "📍", "media": "📺", "messages": "💬", "other": "🧩",
    "photo": "🖼️", "pin": "📌", "poll": "📊", "previews": "🔍",
    "rtl": "↩️", "sticker": "✨", "url": "🔗", "username": "👤",
    "video": "🎥", "voice": "🎙️", "text": "📝"
}

BOT_OWNER_ID = 8459937381

# ------------------------------
# 💾 DATA LOAD / SAVE
# ------------------------------

def load_lock_data():
    try:
        if os.path.exists(LOCK_DATA_FILE):
            with open(LOCK_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except:
        return {}


def save_lock_data():
    try:
        with open(LOCK_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(lock_status, f, indent=4, ensure_ascii=False)
    except:
        pass


lock_status = load_lock_data()
atexit.register(save_lock_data)

# ------------------------------
# 🛡 PERMISSION HELPERS
# ------------------------------

async def check_admin_permission(message: Message) -> bool:
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Always treat bot owner as admin
        if user_id == BOT_OWNER_ID:
            return True

        # Directly get chat member and check status
        try:
            member = await app.get_chat_member(chat_id, user_id)
            status = member.status
            
            if status in [member.status.ADMINISTRATOR, member.status.OWNER]:
                return True
            return False
            
        except Exception as e:
            print(f"Admin check error: {e}")
            return False

    except Exception as e:
        print(f"Admin permission error: {e}")
        return False

async def check_owner_or_creator(message: Message) -> bool:
    try:
        # Check if message.from_user exists
        if not message.from_user:
            return False
            
        user = message.from_user
        chat = message.chat

        # Bot owner bypass
        if user.id == BOT_OWNER_ID:
            return True

        # Check actual chat member status
        m = await app.get_chat_member(chat.id, user.id)
        return m.status == m.status.OWNER

    except Exception as e:
        print("Owner Check Error:", e)
        return False

def set_metadata(chat_id: str, message: Message):
    try:
        lock_status.setdefault(chat_id, {})["_updated_by"] = (
            message.from_user.username
            or message.from_user.first_name
            or str(message.from_user.id)
        )
        lock_status.setdefault(chat_id, {})["_updated_at"] = datetime.utcnow().isoformat()
    except:
        pass

# ------------------------------
# 🔒 LOCK COMMAND
# ------------------------------

@app.on_message(filters.command(["lock", "lock@anniexrobot"]) & filters.group)
@language
async def lock_cmd(client, message: Message, _):
    
    # SIMPLE ADMIN CHECK
    try:
        user = await app.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in [user.status.ADMINISTRATOR, user.status.OWNER]:
            if message.from_user.id != BOT_OWNER_ID:
                return await message.reply_text("⛔ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴀʟʟᴏᴡᴇᴅ!")
    except:
        return await message.reply_text("⛔ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴀʟʟᴏᴡᴇᴅ!")

    try:
        chat_id = str(message.chat.id)
        parts = message.text.split(maxsplit=1)

        if len(parts) < 2:
            return await message.reply_text("❌ ᴜꜱᴇ: /lock <type>")

        ltype = parts[1].lower()

        if ltype not in LOCKABLES:
            return await message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ʟᴏᴄᴋ ᴛʏᴘᴇ!")

        # 🔥 FULL GROUP LOCK
        if ltype == "all":
            for t in LOCKABLES:
                if t != "all":
                    lock_status.setdefault(chat_id, {})[t] = True

            set_metadata(chat_id, message)
            save_lock_data()

            try:
                await app.set_chat_permissions(
                    message.chat.id,
                    ChatPermissions()
                )
            except:
                pass

            return await message.reply_text("🔒✨ ᴀʟʟ ʟᴏᴄᴋᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ!")

        # 📸 MEDIA LOCK
        if ltype == "media":
            for t in [
                "photo", "video", "audio", "voice",
                "document", "sticker", "gif", "media"
            ]:
                lock_status.setdefault(chat_id, {})[t] = True

            set_metadata(chat_id, message)
            save_lock_data()

            return await message.reply_text("🔒✨ ᴍᴇᴅɪᴀ ʟᴏᴄᴋᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ!")

        # SINGLE TYPE LOCK
        lock_status.setdefault(chat_id, {})[ltype] = True
        set_metadata(chat_id, message)
        save_lock_data()

        emoji = EMOJI.get(ltype, "🔒")
        return await message.reply_text(f"{emoji}✨ {ltype} ʟᴏᴄᴋᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ!")

    except Exception as e:
        print("Lock Error:", e)
        return await message.reply_text("❌ ᴇʀʀᴏʀ!")


# ------------------------------
# 🔓 UNLOCK COMMAND
# ------------------------------

@app.on_message(filters.command(["unlock", "unlock@anniexrobot"]) & filters.group)
@language
async def unlock_cmd(client, message: Message, _):
    
    # SIMPLE ADMIN CHECK
    try:
        user = await app.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in [user.status.ADMINISTRATOR, user.status.OWNER]:
            if message.from_user.id != BOT_OWNER_ID:
                return await message.reply_text("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ!")
    except:
        return await message.reply_text("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ!")

    try:
        chat_id = str(message.chat.id)
        parts = message.text.split(maxsplit=1)

        if len(parts) < 2:
            return await message.reply_text("❌ ᴜꜱᴇ: /unlock <type>")

        ltype = parts[1].lower()

        # FULL GROUP UNLOCK
        if ltype == "all":
            # Save lockadmin status and media locks before clearing
            lockadmin_status = lock_status.get(chat_id, {}).get("_lockadmin", False)
            silent_status = lock_status.get(chat_id, {}).get("_silent", False)
            
            # Save media locks if lockadmin is ON
            media_locks = {}
            if lockadmin_status:
                media_types = ["photo", "video", "audio", "voice", "document", "sticker", "gif", "media"]
                for media_type in media_types:
                    if lock_status.get(chat_id, {}).get(media_type):
                        media_locks[media_type] = True
            
            # Clear all locks
            lock_status.pop(chat_id, None)
            
            # Restore lockadmin, silent mode, and media locks
            if lockadmin_status:
                lock_status.setdefault(chat_id, {})["_lockadmin"] = lockadmin_status
                for media_type, status in media_locks.items():
                    lock_status.setdefault(chat_id, {})[media_type] = status
                    
            if silent_status:
                lock_status.setdefault(chat_id, {})["_silent"] = silent_status
                
            save_lock_data()

            try:
                await app.set_chat_permissions(
                    message.chat.id,
                    ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True
                    )
                )
            except:
                pass

            return await message.reply_text("🔓✨ ᴀʟʟ ᴜɴʟᴏᴄᴋᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ!")

        # MEDIA UNLOCK
        if ltype == "media":
            for t in [
                "photo", "video", "audio", "voice",
                "document", "sticker", "gif", "media"
            ]:
                if chat_id in lock_status:
                    lock_status[chat_id].pop(t, None)

            set_metadata(chat_id, message)
            save_lock_data()

            return await message.reply_text("🔓✨ ᴍᴇᴅɪᴀ ᴜɴʟᴏᴄᴋᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ!")

        # SINGLE TYPE UNLOCK
        if chat_id in lock_status and ltype in lock_status[chat_id]:
            lock_status[chat_id].pop(ltype, None)
            set_metadata(chat_id, message)
            save_lock_data()

            emoji = EMOJI.get(ltype, "🔓")
            return await message.reply_text(f"{emoji}✨ {ltype} ᴜɴʟᴏᴄᴋᴇᴅ!")

        return await message.reply_text("ℹ️ ɴᴏᴛ ʟᴏᴄᴋᴇᴅ!")

    except Exception as e:
        print("Unlock Error:", e)
        return await message.reply_text("❌ ᴇʀʀᴏʀ!")


# ------------------------------
# 🔓 UNLOCK ALL
# ------------------------------

@app.on_message(filters.command(["unlockall", "unlockall@anniexrobot"]) & filters.group)
@language
async def unlockall_cmd(client, message: Message, _):
    
    # SIMPLE ADMIN CHECK
    try:
        user = await app.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in [user.status.ADMINISTRATOR, user.status.OWNER]:
            if message.from_user.id != BOT_OWNER_ID:
                return await message.reply_text("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ!")
    except:
        return await message.reply_text("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ!")

    chat_id = str(message.chat.id)
    
    # Save lockadmin status and media locks before clearing
    lockadmin_status = lock_status.get(chat_id, {}).get("_lockadmin", False)
    silent_status = lock_status.get(chat_id, {}).get("_silent", False)
    
    # Save media locks if lockadmin is ON
    media_locks = {}
    if lockadmin_status:
        media_types = ["photo", "video", "audio", "voice", "document", "sticker", "gif", "media"]
        for media_type in media_types:
            if lock_status.get(chat_id, {}).get(media_type):
                media_locks[media_type] = True
    
    # Clear all locks
    lock_status.pop(chat_id, None)
    
    # Restore lockadmin, silent mode, and media locks
    if lockadmin_status:
        lock_status.setdefault(chat_id, {})["_lockadmin"] = lockadmin_status
        for media_type, status in media_locks.items():
            lock_status.setdefault(chat_id, {})[media_type] = status
            
    if silent_status:
        lock_status.setdefault(chat_id, {})["_silent"] = silent_status
        
    save_lock_data()

    try:
        await app.set_chat_permissions(
            message.chat.id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
    except:
        pass

    return await message.reply_text("🔓✨ ᴀʟʟ ᴜɴʟᴏᴄᴋᴇᴅ!")

@app.on_message(filters.command(["locktypes", "locktypes@anniexrobot"]) & filters.group)
async def locktypes_cmd(client, message):

    text = "🔐 Available Lock Types:\n\n"

    for t in LOCKABLES:
        emoji = EMOJI.get(t, "🔸")
        text += f"{emoji} {t}\n"

    await message.reply_text(text)


# ------------------------------
# 📊 ACTIVE LOCKS
# ------------------------------

@app.on_message(filters.command(["locks", "locks@anniexrobot"]) & filters.group)
@language
async def locks_cmd(client, message: Message, _):
    
    # SIMPLE ADMIN CHECK
    try:
        user = await app.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in [user.status.ADMINISTRATOR, user.status.OWNER]:
            if message.from_user.id != BOT_OWNER_ID:
                return await message.reply_text("⛔ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴀʟʟᴏᴡᴇᴅ!")
    except:
        return await message.reply_text("⛔ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴀʟʟᴏᴡᴇᴅ!")

    chat_id = str(message.chat.id)
    data = lock_status.get(chat_id, {})

    active = [k for k, v in data.items() if v and not str(k).startswith("_")]

    if not active:
        return await message.reply_text("✨ ɴᴏ ᴀᴄᴛɪᴠᴇ ʟᴏᴄᴋꜱ!")

    text = "🔐 ᴀᴄᴛɪᴠᴇ ʟᴏᴄᴋꜱ:\n\n"
    for key in active:
        emoji = EMOJI.get(key, "🔸")
        text += f"{emoji} {key}\n"

    await message.reply_text(text)


# ------------------------------
# 📌 FULL LOCK STATUS
# ------------------------------

@app.on_message(filters.command(["lockstatus", "lockstatus@anniexrobot"]) & filters.group)
@language
async def lockstatus_cmd(client, message: Message, _):
    
    # SIMPLE ADMIN CHECK
    try:
        user = await app.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in [user.status.ADMINISTRATOR, user.status.OWNER]:
            if message.from_user.id != BOT_OWNER_ID:
                return await message.reply_text("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ!")
    except:
        return await message.reply_text("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ!")

    chat_id = str(message.chat.id)
    data = lock_status.get(chat_id, {})

    result = "🔐 ꜱᴛʏʟɪꜱʜ ʟᴏᴄᴋ ꜱᴛᴀᴛᴜꜱ:\n\n"

    for key in LOCKABLES:
        if key == "all":
            continue

        emoji = EMOJI.get(key, "🔸")
        status = "🔒" if data.get(key) else "🔓"
        result += f"{emoji} {key} — {status}\n"

    return await message.reply_text(result)


# ------------------------------
# 🔕 SILENT MODE
# ------------------------------

@app.on_message(filters.command(["locksilent", "locksilent@anniexrobot"]) & filters.group)
@language
async def locksilent_cmd(client, message: Message, _):
    
    # SIMPLE ADMIN CHECK
    try:
        user = await app.get_chat_member(message.chat.id, message.from_user.id)
        if user.status not in [user.status.ADMINISTRATOR, user.status.OWNER]:
            if message.from_user.id != BOT_OWNER_ID:
                return await message.reply_text("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ!")
    except:
        return await message.reply_text("⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ!")

    chat_id = str(message.chat.id)
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        mode = lock_status.get(chat_id, {})["_silent"] if chat_id in lock_status and "_silent" in lock_status[chat_id] else False
        return await message.reply_text(
            f"🔕 ꜱɪʟᴇɴᴛ ᴍᴏᴅᴇ: {'ON' if mode else 'OFF'}"
        )

    mode = args[1].lower()

    if mode in ["on", "enable", "yes"]:
        lock_status.setdefault(chat_id, {})["_silent"] = True
        save_lock_data()
        return await message.reply_text("🔕✨ ꜱɪʟᴇɴᴛ ᴍᴏᴅᴇ ᴇɴᴀʙʟᴇᴅ!")

    elif mode in ["off", "disable", "no"]:
        lock_status.setdefault(chat_id, {})["_silent"] = False
        save_lock_data()
        return await message.reply_text("🔔✨ ꜱɪʟᴇɴᴛ ᴍᴏᴅᴇ ᴅɪꜱᴀʙʟᴇᴅ!")

    else:
        return await message.reply_text("❌ ᴜꜱᴇ: /locksilent on/off")


# ------------------------------
# 👀 WATCHER — AUTO DELETE LOCKED CONTENT (COMPLETE FIX)
# ------------------------------

@app.on_message(filters.group, group=69)
async def lock_watcher(client, message: Message):
    try:
        # Skip if no user or bot
        if not message.from_user or message.from_user.is_bot:
            return

        chat_id = str(message.chat.id)
        data = lock_status.get(chat_id, {})
        
        # Skip if no locks active
        if not data:
            return

        # Get user member info
        try:
            user_member = await app.get_chat_member(message.chat.id, message.from_user.id)
            user_status = user_member.status
            user_id = message.from_user.id
        except Exception as e:
            return

        # Check if lockadmin is enabled
        lockadmin_on = data.get("_lockadmin", False)
        silent_mode = data.get("_silent", False)

        # DETERMINE PRIVILEGE
        is_privileged = False
        
        # Bot Owner always privileged (NEVER DELETE BOT OWNER MESSAGES)
        if user_id == BOT_OWNER_ID:
            is_privileged = True
        # Group Creator always privileged
        elif user_status == user_member.status.OWNER:
            is_privileged = True
        # For Admins - check lockadmin setting
        elif user_status == user_member.status.ADMINISTRATOR:
            if lockadmin_on:
                # Lockadmin ON - Admins are NOT privileged
                is_privileged = False
            else:
                # Lockadmin OFF - Admins are privileged
                is_privileged = True
        else:
            # Normal users are never privileged
            is_privileged = False

        # If user is privileged, skip all checks (NEVER DELETE)
        if is_privileged:
            return

        # CHECK LOCKS - Only for non-privileged users
        delete_it = False

        # Full lock check
        if data.get("all"):
            delete_it = True

        # Individual lock checks - COMPLETE LIST
        elif message.text and data.get("text"):
            delete_it = True
        
        elif message.photo and data.get("photo"):
            delete_it = True
        
        elif message.video and data.get("video"):
            delete_it = True
        
        elif message.audio and data.get("audio"):
            delete_it = True
        
        elif message.voice and data.get("voice"):
            delete_it = True
        
        elif message.document and data.get("document"):
            delete_it = True
        
        elif message.sticker and data.get("sticker"):
            delete_it = True
        
        elif getattr(message, "animation", None) and data.get("gif"):
            delete_it = True
        
        elif message.poll and data.get("poll"):
            delete_it = True
        
        elif message.contact and data.get("contact"):
            delete_it = True
        
        elif message.location and data.get("location"):
            delete_it = True
        
        elif message.forward_date and data.get("forward"):
            delete_it = True

        # URL Lock check
        elif (message.text or message.caption) and data.get("url"):
            entities = message.entities or message.caption_entities
            if entities:
                for e in entities:
                    if e.type == MessageEntityType.URL:
                        delete_it = True
                        break

        # USERNAME LOCK CHECK - For @mentions and username tags
        elif (message.text or message.caption) and data.get("username"):
            entities = message.entities or message.caption_entities
            if entities:
                for e in entities:
                    # Check for mention entities (username mentions)
                    if e.type in [MessageEntityType.MENTION, MessageEntityType.TEXT_MENTION]:
                        delete_it = True
                        break

        # BOTS LOCK CHECK - Prevent bot commands and bot messages
        elif message.text and data.get("bots"):
            if message.text.startswith("/") or message.text.startswith("!"):
                delete_it = True

        # BUTTON LOCK CHECK - Inline keyboard buttons
        elif message.reply_markup and data.get("button"):
            delete_it = True

        # INVITE LOCK CHECK - Telegram invite links
        elif (message.text or message.caption) and data.get("invite"):
            if "t.me/" in (message.text or message.caption) or "telegram.me/" in (message.text or message.caption):
                delete_it = True

        # GAME LOCK CHECK
        elif message.game and data.get("game"):
            delete_it = True

        # LOCATION LOCK CHECK (already covered above, but adding separate)
        elif message.location and data.get("location"):
            delete_it = True

        # Media lock (combined check)
        media_types = ["photo", "video", "audio", "voice", "document", "sticker", "gif"]
        if any([getattr(message, mt, None) for mt in media_types]) and data.get("media"):
            delete_it = True

        # Delete message if locked
        if delete_it:
            try:
                await message.delete()

                # Send warning if not silent mode
                if not silent_mode:
                    warn_msg = f"⛔ {message.from_user.mention} ᴛʜɪs ᴄᴏɴᴛᴇɴᴛ ɪs ʟᴏᴄᴋᴇᴅ!"
                    sent_msg = await message.reply_text(warn_msg)
                    await asyncio.sleep(3)
                    await sent_msg.delete()

            except Exception as delete_error:
                print(f"Delete error: {delete_error}")

    except Exception as e:
        if "'Message' object has no attribute 'te'" in str(e):
            pass
        else:
            print(f"Watcher Error: {e}")


# ------------------------------
# 🔐 LOCKADMIN
# ------------------------------

@app.on_message(filters.command(["lockadmin", "lockadmin@anniexrobot"]) & filters.group)
@language
async def lockadmin_cmd(client, message: Message, _):

    if not message.from_user:
        return await message.reply_text("❌ ᴜɴᴀʙʟᴇ ᴛᴏ ɪᴅᴇɴᴛɪꜰʏ ᴜꜱᴇʀ!")

    if not await check_owner_or_creator(message):
        return await message.reply_text(
            "👑 ᴏɴʟʏ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ ᴀɴᴅ ʙᴏᴛ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ!"
        )

    chat_id = str(message.chat.id)
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        current = lock_status.get(chat_id, {}).get("_lockadmin", False)
        return await message.reply_text(
            f"🔑 ʟᴏᴄᴋᴀᴅᴍɪɴ: {'ON' if current else 'OFF'}"
        )

    mode = args[1].lower()

    if mode in ["on", "enable", "yes"]:
        # AUTO LOCK ALL MEDIA TYPES WHEN LOCKADMIN IS ENABLED
        media_types = ["photo", "video", "audio", "voice", "document", "sticker", "gif", "media"]
        for media_type in media_types:
            lock_status.setdefault(chat_id, {})[media_type] = True
        
        # Enable lockadmin
        lock_status.setdefault(chat_id, {})["_lockadmin"] = True
        set_metadata(chat_id, message)
        save_lock_data()
        
        return await message.reply_text("🔑✨ ʟᴏᴄᴋᴀᴅᴍɪɴ ᴇɴᴀʙʟᴇᴅ + ᴀʟʟ ᴍᴇᴅɪᴀ ʟᴏᴄᴋᴇᴅ!")

    elif mode in ["off", "disable", "no"]:
        # Disable lockadmin but don't unlock media
        lock_status.setdefault(chat_id, {})["_lockadmin"] = False
        set_metadata(chat_id, message)
        save_lock_data()
        
        return await message.reply_text("🔑✨ ʟᴏᴄᴋᴀᴅᴍɪɴ ᴅɪꜱᴀʙʟᴇᴅ!")

    else:
        return await message.reply_text("❌ ᴜꜱᴇ: /lockadmin on/off")


# ------------------------------
# ❓ LOCK HELP COMMAND
# ------------------------------

@app.on_message(filters.command(["lockhelp", "lockhelp@anniexrobot"]) & filters.group)
@language
async def lock_help(client, message: Message, _):

    text = """
🔐 ʟᴏᴄᴋ ꜱʏꜱᴛᴇᴍ ʜᴇʟᴘ

✨ Basic Locks
/lock text - 📝 Lock text messages
/lock media - 📺 Lock media (photo/video/sticker/gif/document)
/lock audio - 🎵 Lock audio
/lock voice - 🎙 Lock voice
/lock photo - 🖼 Lock photos
/lock video - 🎥 Lock videos
/lock sticker - ✨ Lock stickers
/lock gif - 🎞 Lock GIFs
/lock document - 📄 Lock files
/lock url - 🔗 Lock external links
/lock username - 👤 Lock username mentions (@username)
/lock forward - 🔄 Lock forwarded messages
/lock contact - 📇 Lock contacts
/lock location - 📍 Lock locations
/lock poll - 📊 Lock polls
/lock bots - 🤖 Lock bot commands
/lock button - 🔘 Lock inline buttons
/lock invite - 🔗 Lock invite links

✨ Full Group Lock
/lock all - 🔐 Completely lock group

✨ Unlock Commands
/unlock <type> - 🔓 Unlock specific type
/unlock media - 🔓 Unlock all media
/unlockall - 🔓 Fully unlock group

✨ Lock Info
/locks - 📌 See active locks
/lockstatus - 📊 Full lock status

✨ Silent Mode
/locksilent on - 🔕 No warnings (only auto delete)
/locksilent off - 🔔 Show warning

✨ Admin-Only Control
/lockadmin on - 🔑 Auto lock all media + Admins also locked
/lockadmin off - 🔓 Only members affected

👑 Bot Owner & Group Creator: NEVER DELETED
👥 Admins: Respect lockadmin setting
👤 Members: Always affected by locks
"""

    await message.reply_text(text)
