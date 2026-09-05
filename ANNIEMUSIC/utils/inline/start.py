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

def _e(eid: int, fb: str) -> str:
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

def start_panel(_):
    return [
        [
            InlineKeyboardButton(
                text=f"{_e(_PE['add'], '➕')} {_['S_B_1']}",
                url=f"https://t.me/{app.username}?startgroup=true",
            ),
            InlineKeyboardButton(
                text=f"{_e(_PE['channel'], '📢')} {_['S_B_2']}",
                url=config.SUPPORT_CHANNEL,
            ),
        ],
    ]

def private_panel(_):
    return [
        [
            InlineKeyboardButton(
                text=f"{_e(_PE['add'], '➕')} {_['S_B_1']}",
                url=f"https://t.me/{app.username}?startgroup=true",
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{_e(_PE['owner'], '👑')} {_['S_B_7']}",
                user_id=config.OWNER_ID,
            ),
            InlineKeyboardButton(
                text=f"{_e(_PE['support'], '❄️')} {_['S_B_4']}",
                url=config.SUPPORT_CHAT,
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{_e(_PE['help'], '✦')} {_['S_B_3']}",
                callback_data="open_help",
            ),
        ],
    ]
