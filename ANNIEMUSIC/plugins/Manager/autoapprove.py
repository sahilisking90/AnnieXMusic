print("AUTOAPPROVE PLUGIN LOADED✅")

from ANNIEMUSIC import app
from pyrogram import filters
from pyrogram.types import (
    ChatJoinRequest,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from ANNIEMUSIC.core.mongo import mongodb


# ✦━━━━━━━━━━━━━━ MONGO DB ━━━━━━━━━━━━━✦
autoapprove_db = mongodb.autoapprove


def fancy(text: str) -> str:
    """Convert normal text to fancy small caps style"""
    mapping = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ',
        'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
        'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ',
        'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ꜰ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ'
    }
    return ''.join(mapping.get(c, c) for c in text)


# ✦━━━━━━━━━━━━━━ MONGO DB FUNCTIONS ━━━━━━━━━━━━━✦
async def autoapprove_on(chat_id: int):
    await autoapprove_db.update_one(
        {"chat_id": chat_id},
        {"$set": {"auto": True}},
        upsert=True,
    )


async def autoapprove_off(chat_id: int):
    await autoapprove_db.update_one(
        {"chat_id": chat_id},
        {"$set": {"auto": False}},
        upsert=True,
    )


async def is_autoapprove_on(chat_id: int) -> bool:
    doc = await autoapprove_db.find_one({"chat_id": chat_id})
    return doc.get("auto", False) if doc else False


# ✦━━━━━━━━━━━━━━ ADMIN CHECK ━━━━━━━━━━━━━✦
async def is_admin(chat_id: int, user_id: int):
    try:
        member = await app.get_chat_member(chat_id, user_id)
        status = str(member.status).lower()
        return "administrator" in status or "creator" in status or "owner" in status
    except:
        return False


# ✦━━━━━━━━━━━━━━ /AUTOAPPROVE COMMAND ━━━━━━━━━━━━━✦
@app.on_message(filters.command(["autoapprove"]) & filters.group)
async def autoapprove_cmd(_, message):
    chat_id = message.chat.id
    user = message.from_user

    if not await is_admin(chat_id, user.id):
        return await message.reply_text(fancy("you need admin rights to use this command."))

    if len(message.command) > 1:
        arg = message.command[1].lower()
        if arg == "on":
            await autoapprove_on(chat_id)
            return await message.reply_text(fancy("auto approve is now enabled ✅"))
        elif arg == "off":
            await autoapprove_off(chat_id)
            return await message.reply_text(fancy("auto approve is now disabled ❌"))

    status = await is_autoapprove_on(chat_id)
    await message.reply_text(
        f"""
✦ {fancy('join request manager')} ✦

❍ {fancy('status')} : {'ᴏɴ ✅' if status else 'ᴏꜰꜰ ❌'}

❍ {fancy('commands')}

• /autoapprove on
• /autoapprove off
"""
    )


# ✦━━━━━━━━━━━━━━ JOIN REQUEST HANDLER ━━━━━━━━━━━━━✦
@app.on_chat_join_request()
async def handle_join_request(_, req: ChatJoinRequest):
    chat_id = req.chat.id
    user = req.from_user

    if await is_autoapprove_on(chat_id):
        try:
            await app.approve_chat_join_request(chat_id, user.id)
            await app.send_message(
                user.id,
                fancy(f"your join request for {req.chat.title} has been auto approved ✅\n\nwelcome! 🎉"),
            )
        except Exception as e:
            print(f"Error auto approving: {e}")
    else:
        try:
            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "ᴀᴄᴄᴇᴘᴛ ✅",
                            callback_data=f"approve_{chat_id}_{user.id}",
                        ),
                        InlineKeyboardButton(
                            "ʀᴇᴊᴇᴄᴛ ❌",
                            callback_data=f"decline_{chat_id}_{user.id}",
                        ),
                    ]
                ]
            )
            await app.send_message(
                chat_id,
                f"""
✦ ɴᴇᴡ ᴊᴏɪɴ ʀᴇQᴜᴇsᴛ ✦

👤 {user.mention}
🆔 `{user.id}`

⦿ sᴇʟᴇᴄᴛ ᴀɴ ᴀᴄᴛɪᴏɴ ʙᴇʟᴏᴡ.
""",
                reply_markup=buttons,
            )
        except Exception as e:
            print(f"Error sending manual request: {e}")


# ✦━━━━━━━━━━━━━━ CALLBACK HANDLER ━━━━━━━━━━━━━✦
@app.on_callback_query(filters.regex(r"^(approve|decline)_"))
async def handle_join_callback(_, callback: CallbackQuery):
    data = callback.data

    if data.startswith("approve_") or data.startswith("decline_"):
        action, chat_id_str, user_id_str = data.split("_")
        chat_id = int(chat_id_str)
        user_id = int(user_id_str)

        if not await is_admin(chat_id, callback.from_user.id):
            return await callback.answer(fancy("you are not an admin."), show_alert=True)

        if action == "approve":
            try:
                await app.approve_chat_join_request(chat_id, user_id)
                await callback.message.edit_text(
                    f"""
✦ {fancy('join request update')} ✦

🆔 `{user_id}`

{fancy('status')} : {fancy('accepted')} ✅
"""
                )
                await callback.answer(fancy("user approved successfully!"), show_alert=True)
            except Exception as e:
                await callback.answer(fancy(f"error: {str(e)}"), show_alert=True)

        elif action == "decline":
            try:
                await app.decline_chat_join_request(chat_id, user_id)
                await callback.message.edit_text(
                    f"""
✦ {fancy('join request update')} ✦

🆔 `{user_id}`

{fancy('status')} : {fancy('rejected')} ❌
"""
                )
                await callback.answer(fancy("user declined successfully!"), show_alert=True)
            except Exception as e:
                await callback.answer(fancy(f"error: {str(e)}"), show_alert=True)
