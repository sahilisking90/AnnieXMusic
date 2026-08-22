from pyrogram import filters
from pyrogram.types import Message
from ANNIEMUSIC.utils.admin_check import is_admin
from ANNIEMUSIC import app
from ANNIEMUSIC.core.mongo import mongodb
import asyncio

db = mongodb.blacklist_words


@app.on_message(filters.command(["addblacklistword", "addbw"]) & filters.group)
async def add_blacklist_word(_, message: Message):

    if not await is_admin(message):
        await message.delete()  # Command delete in 1 second
        msg = await message.reply_text(
            "⦿ ʏᴏᴜ ɴᴇᴇᴅ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ."
        )
        await asyncio.sleep(10)
        await msg.delete()
        return

    if len(message.command) < 2:
        await message.delete()  # Command delete in 1 second
        msg = await message.reply_text(
            "⦿ ᴜsᴀɢᴇ :\n\n<code>/addblacklistword word</code>"
        )
        await asyncio.sleep(10)
        await msg.delete()
        return

    word = message.command[1].lower()
    await message.delete()  # Command delete in 1 second

    data = await db.find_one({"chat_id": message.chat.id})

    if not data:
        await db.insert_one(
            {
                "chat_id": message.chat.id,
                "words": [word]
            }
        )
    else:
        if word in data.get("words", []):
            msg = await message.reply_text(
                f"⦿ <code>{word}</code> ɪs ᴀʟʀᴇᴀᴅʏ ʙʟᴀᴄᴋʟɪsᴛᴇᴅ."
            )
            await asyncio.sleep(10)
            await msg.delete()
            return

        await db.update_one(
            {"chat_id": message.chat.id},
            {"$push": {"words": word}}
        )

    msg = await message.reply_text(
        f"⦿ ᴀᴅᴅᴇᴅ ᴛᴏ ʙʟᴀᴄᴋʟɪsᴛ\n\n<code>{word}</code>"
    )
    await asyncio.sleep(10)
    await msg.delete()


@app.on_message(filters.command(["delblacklistword", "delbw"]) & filters.group)
async def del_blacklist_word(_, message: Message):

    if not await is_admin(message):
        await message.delete()  # Command delete in 1 second
        msg = await message.reply_text(
            "⦿ ʏᴏᴜ ɴᴇᴇᴅ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ."
        )
        await asyncio.sleep(10)
        await msg.delete()
        return

    if len(message.command) < 2:
        await message.delete()  # Command delete in 1 second
        msg = await message.reply_text(
            "⦿ ᴜsᴀɢᴇ :\n\n<code>/delblacklistword word</code>"
        )
        await asyncio.sleep(10)
        await msg.delete()
        return

    word = message.command[1].lower()
    await message.delete()  # Command delete in 1 second

    await db.update_one(
        {"chat_id": message.chat.id},
        {"$pull": {"words": word}}
    )

    msg = await message.reply_text(
        f"⦿ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ʙʟᴀᴄᴋʟɪsᴛ\n\n<code>{word}</code>"
    )
    await asyncio.sleep(10)
    await msg.delete()


@app.on_message(filters.command(["blacklistwords", "bwlist"]) & filters.group)
async def blacklist_words(_, message: Message):
    await message.delete()  # Command delete in 1 second
    
    data = await db.find_one({"chat_id": message.chat.id})

    if not data or not data.get("words"):
        msg = await message.reply_text(
            "⦿ ɴᴏ ʙʟᴀᴄᴋʟɪsᴛᴇᴅ ᴡᴏʀᴅs."
        )
        await asyncio.sleep(10)
        await msg.delete()
        return

    text = "⦿ ʙʟᴀᴄᴋʟɪsᴛ ᴡᴏʀᴅs\n\n"

    for word in data["words"]:
        text += f"• <code>{word}</code>\n"

    msg = await message.reply_text(text)
    await asyncio.sleep(10)
    await msg.delete()


@app.on_message(filters.command(["blacklisthelp", "bwhelp"]))
async def blacklist_help(_, message: Message):
    await message.delete()  # Command delete in 1 second
    
    msg = await message.reply_text(
        "⦿ ʙʟᴀᴄᴋʟɪsᴛ ᴡᴏʀᴅ sʏsᴛᴇᴍ\n\n"
        "➥ /addbw mc\n"
        "➥ /delbw mc\n"
        "➥ /bwlist\n\n"
        "⦿ ᴇxᴀᴍᴘʟᴇ\n\n"
        "ᴀᴅᴍɪɴ : /addbw mc\n"
        "ᴜsᴇʀ : ᴛᴜ ᴍᴄ ʜᴀɪ\n"
        "ʙᴏᴛ : (ᴍᴇssᴀɢᴇ ᴅᴇʟᴇᴛᴇᴅ)"
    )
    await asyncio.sleep(10)
    await msg.delete()


@app.on_message(filters.text & filters.group, group=20)
async def blacklist_filter(_, message: Message):
    if not message.text or not message.from_user:
        return

    try:
        member = await app.get_chat_member(
            message.chat.id,
            message.from_user.id
        )

        status = str(member.status).lower()

        if (
            "administrator" in status
            or "creator" in status
            or "owner" in status
        ):
            return

    except Exception:
        pass

    data = await db.find_one({"chat_id": message.chat.id})

    if not data:
        return

    text = message.text.lower()

    for word in data.get("words", []):
        if word.lower() in text:
            try:
                await message.delete()
                
                # Get user's first name
                user_name = message.from_user.first_name or "User"
                user_id = message.from_user.id
                
                # Proper mention with hyperlink (same as VC logger)
                mention = f'<a href="tg://user?id={user_id}"><b>{user_name}</b></a>'
                
                # Send notification with proper mention
                notification = await message.reply_text(
                    f"⦿ ⚠️ <b>ʙʟᴀᴄᴋʟɪsᴛᴇᴅ ᴡᴏʀᴅ ᴅᴇᴛᴇᴄᴛᴇᴅ</b>\n\n"
                    f"• <b>ᴜsᴇʀ :</b> {mention}\n"
                    f"• <b>ᴡᴏʀᴅ :</b> <code>{word}</code>\n"
                    f"• <b>ᴀᴄᴛɪᴏɴ :</b> ᴍᴇssᴀɢᴇ ᴅᴇʟᴇᴛᴇᴅ"
                )
                await asyncio.sleep(4)  # 3 seconds me delete
                await notification.delete()
            except Exception:
                pass
            return
