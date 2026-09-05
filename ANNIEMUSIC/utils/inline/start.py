from pyrogram.types import InlineKeyboardButton

import config
from ANNIEMUSIC import app

_PE = {
    "add":     5467641505525016018,
    "channel": 6197411888553270114,
    "help":    6122805733936342496,
    "support": 6183633702187176982,
    "owner":   5193037303961920951,
}

def start_panel(_):
    return [
        [
            InlineKeyboardButton(
                text=_['S_B_1'],
                url=f"https://t.me/{app.username}?startgroup=true",
                icon_custom_emoji_id=_PE["add"]
            ),
            InlineKeyboardButton(
                text=_['S_B_2'],
                url=config.SUPPORT_CHANNEL,
                icon_custom_emoji_id=_PE["channel"]
            ),
        ],
    ]

def private_panel(_):
    return [
        [
            InlineKeyboardButton(
                text=_['S_B_1'],
                url=f"https://t.me/{app.username}?startgroup=true",
                icon_custom_emoji_id=_PE["add"]
            ),
        ],
        [
            InlineKeyboardButton(
                text=_['S_B_7'],
                user_id=config.OWNER_ID,
                icon_custom_emoji_id=_PE["owner"]
            ),
            InlineKeyboardButton(
                text=_['S_B_4'],
                url=config.SUPPORT_CHAT,
                icon_custom_emoji_id=_PE["support"]
            ),
        ],
        [
            InlineKeyboardButton(
                text=_['S_B_3'],
                callback_data="open_help",
                icon_custom_emoji_id=_PE["help"]
            ),
        ],
    ]
