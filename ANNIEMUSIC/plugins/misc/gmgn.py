import os
import io
import re
import math
import random
import asyncio
import datetime
import html

from zoneinfo import ZoneInfo

from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

from config import BANNED_USERS, SUPPORT_CHAT, BOT_NAME
from ANNIEMUSIC import app


# =========================================================
# CONFIG
# =========================================================

TIMEZONE = os.environ.get("TIMEZONE", "Asia/Kolkata")

FONT_PATH  = os.environ.get("FONT_PATH",  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
FONT_PATH2 = os.environ.get("FONT_PATH2", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

ALLOW_OUT_OF_TIME_REPLY = bool(os.environ.get("ALLOW_OUT_OF_TIME_REPLY", "").strip())


# =========================================================
# GENDER DETECTION SYSTEM
# =========================================================

# Girl names (ending patterns and common girl names)
GIRL_ENDINGS = ['a', 'i', 'e', 'y', 'aa', 'ee', 'u']
GIRL_NAMES = [
    'priya', 'neha', 'pooja', 'ritu', 'anjali', 'kavita', 'sonal', 'monica',
    'sneha', 'arti', 'pallavi', 'reshma', 'kajal', 'divya', 'nisha', 'jyoti',
    'savita', 'rekha', 'meena', 'seema', 'geeta', 'sita', 'radha', 'laxmi',
    'sakshi', 'payal', 'soniya', 'shreya', 'riya', 'siya', 'tina', 'mina',
    'sima', 'nidhi', 'ekta', 'shanti', 'maya', 'aditi', 'ishita', 'tanvi',
    'khushi', 'aanya', 'anaya', 'myra', 'aadhya', 'navya', 'anya', 'diya',
]

# Boy names (ending patterns and common boy names)
BOY_ENDINGS = ['n', 't', 'r', 'k', 'sh', 's', 'v', 'j', 'p']
BOY_NAMES = [
    'raj', 'rahul', 'amit', 'rohit', 'vikas', 'sanjay', 'vijay', 'ajay',
    'suresh', 'mahesh', 'ramesh', 'dinesh', 'mukesh', 'rajesh', 'kunal',
    'ankit', 'deepak', 'sunil', 'anil', 'ravi', 'mohan', 'sohan', 'mohit',
    'rohan', 'sahil', 'ritik', 'arjun', 'krishna', 'shivam', 'aditya', 'vivek',
    'manish', 'pankaj', 'alok', 'ranjan', 'avinash', 'prashant', 'vishal',
    'sameer', 'naveen', 'parth', 'yash', 'ved', 'kabir', 'aryan', 'vihaan',
]

def detect_gender(name):
    """Detect gender based on name patterns"""
    if not name:
        return "neutral"
    
    name_lower = name.lower().strip()
    
    # Check in girl names list
    if name_lower in GIRL_NAMES:
        return "girl"
    
    # Check in boy names list
    if name_lower in BOY_NAMES:
        return "boy"
    
    # Check endings for girl names (ends with a, i, e, y, aa, ee, u)
    for ending in GIRL_ENDINGS:
        if name_lower.endswith(ending):
            return "girl"
    
    # Check endings for boy names
    for ending in BOY_ENDINGS:
        if name_lower.endswith(ending):
            return "boy"
    
    return "neutral"


# =========================================================
# STYLISH TEXT CONVERTER (Small caps generator)
# =========================================================

def to_smallcaps(text):
    """Convert normal text to Unicode small capitals"""
    smallcaps_map = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ',
        'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
        'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ',
        'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ',
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ'
    }
    return ''.join(smallcaps_map.get(c, c) for c in text)


# =========================================================
# DATASETS — MORNING / AFTERNOON / NIGHT
# =========================================================

# DEFAULT MORNING LINES
GOOD_MORNING_LINES = [
    ["☀️ ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ ☀️",   "ʜᴀᴠᴇ ᴀ ɢʀᴇᴀᴛ ᴅᴀʏ"],
    ["🌸 ʀɪsᴇ ᴀɴᴅ sʜɪɴᴇ 🌸",  "ɴᴇᴡ ʙᴇɢɪɴɴɪɴɢ ᴀᴡᴀɪᴛs"],
    ["✨ ɴᴇᴡ ᴍᴏʀɴɪɴɢ ✨",       "ɴᴇᴡ ʜᴏᴘᴇ ɴᴇᴡ ᴊᴏʏ"],
    ["☕ ɢᴏᴏᴅ ᴠɪʙᴇs ☕",         "sᴛᴀʀᴛ ғʀᴇsʜ sᴛᴀʏ ʙʟᴇssᴇᴅ"],
    ["🌿 ʙʀᴇᴀᴛʜᴇ 🌿",            "sᴍɪʟᴇ ᴍᴏʀᴇ ᴡᴏʀʀʏ ʟᴇss"],
    ["🌼 ʙᴇᴀᴜᴛɪғᴜʟ ᴍᴏʀɴɪɴɢ 🌼","ʙᴇ ʜᴀᴘᴘʏ ʙᴇ ᴋɪɴᴅ"],
    ["💛 ᴘᴏsɪᴛɪᴠᴇ ᴅᴀʏ 💛",       "ᴇɴᴊᴏʏ ᴇᴠᴇʀʏ ᴍᴏᴍᴇɴᴛ"],
    ["🌞 sᴜɴʀɪsᴇ ᴠɪʙᴇ 🌞",       "sᴛᴀʀᴛ sᴛʀᴏɴɢᴇʀ ᴛᴏᴅᴀʏ"],
    ["🦋 ʜᴀᴘᴘʏ sᴏᴜʟ 🦋",         "ᴋᴇᴇᴘ ɢᴏɪɴɢ ᴋᴇᴇᴘ ɢʟᴏᴡɪɴɢ"],
    ["🌈 ɴᴇᴡ ʜᴏᴘᴇ 🌈",            "ʙᴇ sᴛʀᴏɴɢ ʙᴇ ʏᴏᴜ"],
    ["✨ ᴘᴏsɪᴛɪᴠᴇ ᴍɪɴᴅ ✨",       "ᴘᴏsɪᴛɪᴠᴇ ʟɪғᴇ ᴀʜᴇᴀᴅ"],
    ["🌸 sᴍɪʟᴇ 🌸",               "ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ʜᴀᴘᴘɪɴᴇss"],
    ["☀️ ɢᴏᴏᴅ ᴠɪʙᴇ ☀️",          "ɢᴏᴏᴅ ʟɪғᴇ ɢᴏᴏᴅ ᴅᴀʏ"],
    ["🌿 ᴄᴀʟᴍ ᴍɪɴᴅ 🌿",           "ʙᴇ ᴘᴇᴀᴄᴇғᴜʟ ʙᴇ ɢʀᴀᴛᴇғᴜʟ"],
    ["🔥 ɴᴇᴡ ᴅᴀʏ 🔥",             "ᴍᴀᴋᴇ ɪᴛ ᴄᴏᴜɴᴛ"],
]

# GIRL-SPECIFIC MORNING LINES
GIRL_MORNING_LINES = [
    ["🌸 ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ ᴘʀɪɴᴄᴇss 🌸",   "ʏᴏᴜʀ ᴅᴀʏ sʜɪɴᴇs ᴀs ʙʀɪɢʜᴛ ᴀs ʏᴏᴜ"],
    ["💖 ʀɪsᴇ ᴀɴᴅ sʜɪɴᴇ Qᴜᴇᴇɴ 💖",      "ʙᴇᴀᴜᴛʏ ᴀɴᴅ ɢʀᴀᴄᴇ ᴀᴡᴀɪᴛs ʏᴏᴜ"],
    ["👑 ʙʟᴇssɪɴɢs ғᴏʀ ᴛʜᴇ Qᴜᴇᴇɴ 👑",   "ʜᴀᴠᴇ ᴀ ᴍᴀɢɪᴄᴀʟ ᴅᴀʏ"],
    ["✨ ɢᴏʀɢᴇᴏᴜs ᴍᴏʀɴɪɴɢ ✨",          "ʏᴏᴜ ᴅᴇsᴇʀᴠᴇ ᴛʜᴇ ʙᴇsᴛ"],
]

# BOY-SPECIFIC MORNING LINES
BOY_MORNING_LINES = [
    ["💪 ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ ᴄʜᴀᴍᴘ 💪",        "ᴄᴏɴǫᴜᴇʀ ᴛʜᴇ ᴅᴀʏ ʟɪᴋᴇ ᴀ ᴡᴀʀʀɪᴏʀ"],
    ["🔥 ʀɪsᴇ ᴀɴᴅ ɢʀɪɴᴅ 🔥",             "ʙᴇ sᴛʀᴏɴɢ, ʙᴇ ғɪᴇʀᴄᴇ"],
    ["⚡ ᴘᴏᴡᴇʀ ᴜᴘ ʙʀᴏ ⚡",               "ʟᴇᴛ's ᴄʀᴜsʜ ᴛᴏᴅᴀʏ"],
    ["🚀 ʙʟᴀsᴛ ᴏғғ ᴍᴏʀɴɪɴɢ 🚀",          "sᴜᴄᴄᴇss ᴡᴀɪᴛs ғᴏʀ ʏᴏᴜ"],
]

# DEFAULT AFTERNOON LINES
GOOD_AFTERNOON_LINES = [
    ["☀️ ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ ☀️",   "ᴇɴᴊᴏʏ ʏᴏᴜʀ ᴅᴀʏ"],
    ["🌤️ ɢʀᴇᴀᴛ ᴀғᴛᴇʀɴᴏᴏɴ 🌤️",  "ᴋᴇᴇᴘ sʜɪɴɪɴɢ"],
    ["🍽️ ʟᴜɴᴄʜ ᴛɪᴍᴇ 🍽️",        "ᴇᴀᴛ ᴡᴇʟʟ sᴛᴀʏ ʜᴇᴀʟᴛʜʏ"],
    ["💪 ᴘᴏᴡᴇʀ ᴛɪᴍᴇ 💪",        "ᴄᴏɴǫᴜᴇʀ ᴛʜᴇ ᴅᴀʏ"],
    ["🎯 ᴍɪᴅ ᴅᴀʏ ᴠɪʙᴇ 🎯",       "ᴅᴏɴ'ᴛ sᴛᴏᴘ ɢᴏɪɴɢ"],
    ["☕ ᴇɴᴇʀɢʏ ᴛɪᴍᴇ ☕",        "sᴛᴀʏ ғᴏᴄᴜsᴇᴅ"],
    ["🌟 ᴀғᴛᴇʀɴᴏᴏɴ ʙʟᴇssɪɴɢs 🌟", "ʜᴀᴠᴇ ᴀ ɴɪᴄᴇ ᴛɪᴍᴇ"],
    ["💛 ʙᴇ ᴘʀᴏᴅᴜᴄᴛɪᴠᴇ 💛",      "ᴍᴀᴋᴇ ɪᴛ ᴄᴏᴜɴᴛ"],
    ["🌞 ɴᴏᴏɴ ᴛɪᴍᴇ 🌞",          "ᴇɴᴊᴏʏ ᴛʜᴇ ᴍᴏᴍᴇɴᴛ"],
]

# GIRL-SPECIFIC AFTERNOON LINES
GIRL_AFTERNOON_LINES = [
    ["🌞 ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ ǫᴜᴇᴇɴ 🌞",   "ᴇɴᴊᴏʏ ʏᴏᴜʀ ʙᴇᴀᴜᴛɪғᴜʟ ᴅᴀʏ"],
    ["💎 ʀᴀʏ ᴏғ sᴜɴsʜɪɴᴇ 💎",          "ʏᴏᴜ ᴍᴀᴋᴇ ᴛʜᴇ ᴅᴀʏ ʙʀɪɢʜᴛ"],
    ["👸 ᴘʀɪɴᴄᴇss ᴛɪᴍᴇ 👸",            "ᴛᴀᴋᴇ ᴀ ʙʀᴇᴀᴋ ᴀɴᴅ sᴍɪʟᴇ"],
]

# BOY-SPECIFIC AFTERNOON LINES
BOY_AFTERNOON_LINES = [
    ["💪 ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ ʙʀᴏ 💪",       "ᴋᴇᴇᴘ ᴘᴜsʜɪɴɢ ғᴏʀᴡᴀʀᴅ"],
    ["🔥 ᴅᴏᴍɪɴᴀᴛᴇ ᴛʜᴇ ᴅᴀʏ 🔥",        "ɴᴏᴏɴ ᴘᴏᴡᴇʀ ᴀᴄᴛɪᴠᴀᴛᴇᴅ"],
    ["⚡ ʟᴇᴛ's ɢᴇᴛ ɪᴛ ᴅᴏɴᴇ ⚡",         "ʜᴀʟғ ᴅᴀʏ ᴅᴏɴᴇ, ᴋᴇᴇᴘ ɢᴏɪɴɢ"],
]

# DEFAULT NIGHT LINES
GOOD_NIGHT_LINES = [
    ["🌙 ɢᴏᴏᴅ ɴɪɢʜᴛ 🌙",          "sᴡᴇᴇᴛ ᴅʀᴇᴀᴍs ᴀᴡᴀɪᴛ"],
    ["✨ ʀᴇsᴛ ᴡᴇʟʟ ✨",            "ʀᴇʟᴀx ʏᴏᴜʀ ᴍɪɴᴅ ᴛᴏᴅᴀʏ"],
    ["🌌 ɴɪɢʜᴛ ᴠɪʙᴇ 🌌",           "sʟᴇᴇᴘ ᴘᴇᴀᴄᴇғᴜʟʟʏ"],
    ["💤 sʟᴇᴇᴘ 💤",                "ʀᴇᴄʜᴀʀɢᴇ ғᴏʀ ᴛᴏᴍᴏʀʀᴏᴡ"],
    ["🌠 ᴅʀᴇᴀᴍ ʙɪɢ 🌠",            "ᴛᴏᴍᴏʀʀᴏᴡ ᴡɪʟʟ ʙᴇ ɢʀᴇᴀᴛ"],
    ["🖤 ᴄᴀʟᴍ ɴɪɢʜᴛ 🖤",           "ɴᴏ sᴛʀᴇss ᴛᴏɴɪɢʜᴛ"],
    ["🌃 ɴɪɢʜᴛ sᴋʏ 🌃",            "ᴘᴇᴀᴄᴇ ᴏɴʟʏ"],
    ["💫 ʀᴇsᴛ 💫",                  "ʙᴇ ғʀᴇsʜ ᴛᴏᴍᴏʀʀᴏᴡ"],
    ["🌙 ɴɪɢʜᴛ ᴍᴀɢɪᴄ 🌙",          "sʟᴇᴇᴘ ᴡᴇʟʟ"],
    ["✨ ʀᴇʟᴀx ✨",                 "ʀᴇᴄᴏᴠᴇʀ ᴀɴᴅ ʀɪsᴇ"],
]

# GIRL-SPECIFIC NIGHT LINES
GIRL_NIGHT_LINES = [
    ["🌙 ɢᴏᴏᴅ ɴɪɢʜᴛ ᴅʀᴇᴀᴍ ǫᴜᴇᴇɴ 🌙",   "ᴅʀᴇᴀᴍ ᴏғ sᴛᴀʀs ᴀɴᴅ ғᴀɪʀɪᴇs"],
    ["💤 sʟᴇᴇᴘ ᴡᴇʟʟ ᴘʀɪɴᴄᴇss 💤",       "ʀᴇsᴛ ᴛʜᴏsᴇ ᴘʀᴇᴛᴛʏ ᴇʏᴇs"],
    ["✨ ᴍᴀʏ ʏᴏᴜʀ ᴅʀᴇᴀᴍs ʙᴇ sᴡᴇᴇᴛ ✨", "ɴɪɢʜᴛ ɴʏᴍᴘʜ ᴀᴡᴀɪᴛs"],
]

# BOY-SPECIFIC NIGHT LINES
BOY_NIGHT_LINES = [
    ["🌙 ɢᴏᴏᴅ ɴɪɢʜᴛ ᴄʜᴀᴍᴘ 🌙",           "ʀᴇᴄʜᴀʀɢᴇ ғᴏʀ ᴛᴏᴍᴏʀʀᴏᴡ's ᴡɪɴ"],
    ["💪 ʀᴇsᴛ ᴡᴇʟʟ ᴡᴀʀʀɪᴏʀ 💪",          "ᴛᴏᴍᴏʀʀᴏᴡ ɪs ᴀ ɴᴇᴡ ʙᴀᴛᴛʟᴇ"],
    ["⚡ ᴘᴏᴡᴇʀ ᴅᴏᴡɴ ⚡",                 "sʟᴇᴇᴘ ᴛɪɢʜᴛ ʙʀᴏᴛʜᴇʀ"],
]

# WRONG TIME MESSAGES
WRONG_MORNING = [
    "ᴀʙʜɪ ɴɪɢʜᴛ ʜᴀɪ ʙʜᴀɪ",
    "ᴀʟᴀʀᴍ ʙʜɪ sᴏ ʀᴀʜᴀ ʜᴀɪ",
    "ᴛɪᴍɪɴɢ ᴛʜᴏᴅɪ ɢᴀʟᴀᴛ ʜᴀɪ",
    "ᴄʜᴀɪ ᴘɪʟᴏ ᴘᴇʜʟᴇ",
]

WRONG_AFTERNOON = [
    "ᴀʙʜɪ ᴍᴏʀɴɪɴɢ ʜᴀɪ ʙʜᴀɪ",
    "ᴅᴜᴘʜᴇʀ ᴍᴇɪɴ ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ ʙᴏʟᴛᴇ ʜᴀɪ",
    "ᴛʜᴏᴅᴀ ɪɴᴛᴢᴀᴀʀ ᴋᴀʀᴏ",
    "ᴀʙʜɪ sᴜʙᴀʜ ʜᴀɪ",
]

WRONG_NIGHT = [
    "ᴀʙʜɪ ᴅɪɴ ʜᴀɪ ʏᴀᴀʀ",
    "sʟᴇᴇᴘ ᴍᴏᴅᴇ ᴀʙʜɪ ᴏғғ ʜᴀɪ",
    "ɴɪɢʜᴛ ᴀʙʜɪ ɴᴀʜɪ ʜᴜᴀ",
    "ʟᴜɴᴄʜ ᴛɪᴍᴇ ᴄʜᴀʟ ʀᴀʜᴀ ʜᴀɪ",
]


# =========================================================
# PREMIUM THEMES
# =========================================================

MORNING_THEMES = [
    {"top": (255, 140, 0),   "bot": (255, 60, 60),   "acc": (255, 220, 100)},
    {"top": (67, 233, 123),  "bot": (56, 189, 248),  "acc": (200, 255, 200)},
    {"top": (255, 94, 98),   "bot": (255, 195, 113), "acc": (255, 240, 180)},
    {"top": (250, 112, 154), "bot": (254, 225, 64),  "acc": (255, 200, 255)},
    {"top": (79, 172, 254),  "bot": (0, 242, 254),   "acc": (200, 240, 255)},
]

AFTERNOON_THEMES = [
    {"top": (255, 165, 0),   "bot": (255, 215, 0),   "acc": (255, 255, 150)},
    {"top": (255, 140, 0),   "bot": (255, 200, 100), "acc": (255, 240, 180)},
    {"top": (240, 128, 0),   "bot": (255, 180, 80),  "acc": (255, 220, 120)},
    {"top": (255, 120, 0),   "bot": (255, 160, 50),  "acc": (255, 200, 100)},
]

NIGHT_THEMES = [
    {"top": (15, 12, 41),    "bot": (48, 43, 99),    "acc": (150, 100, 255)},
    {"top": (20, 30, 70),    "bot": (90, 30, 120),   "acc": (180, 120, 255)},
    {"top": (10, 10, 40),    "bot": (30, 10, 60),    "acc": (100, 80, 220)},
    {"top": (5, 5, 30),      "bot": (40, 20, 80),    "acc": (200, 150, 255)},
    {"top": (20, 20, 60),    "bot": (70, 30, 100),   "acc": (160, 100, 255)},
]


# =========================================================
# REGEX
# =========================================================

GM = re.compile(r"\b(gm|good\s*morning|morning)\b", re.I)
GA = re.compile(r"\b(ga|good\s*afternoon|afternoon)\b", re.I)
GN = re.compile(r"\b(gn|good\s*night|night)\b", re.I)


# =========================================================
# TIME CHECK
# =========================================================

def is_morning(dt):
    return 4 <= dt.hour < 12

def is_afternoon(dt):
    return 12 <= dt.hour < 17

def is_night(dt):
    return dt.hour >= 20 or dt.hour < 4


# =========================================================
# FONT LOADER
# =========================================================

def font(size, bold=True):
    path = FONT_PATH if bold else FONT_PATH2
    try:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    except Exception:
        pass
    return ImageFont.load_default()


# =========================================================
# DRAW STARS (premium particle effect)
# =========================================================

def draw_stars(draw, w, h, theme_acc, count=60):
    for _ in range(count):
        x = random.randint(0, w)
        y = random.randint(0, h)
        r = random.randint(1, 3)
        alpha = random.randint(80, 200)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(*theme_acc, alpha))


# =========================================================
# CIRCULAR CROP FOR PROFILE PHOTO
# =========================================================

def circle_crop(img, size=160):
    img = img.convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    return output


# =========================================================
# PREMIUM BACKGROUND
# =========================================================

def premium_bg(w, h, theme):
    c1, c2 = theme["top"], theme["bot"]
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        r = int(c1[0] + (c2[0] - c1[0]) * y / h)
        g = int(c1[1] + (c2[1] - c1[1]) * y / h)
        b = int(c1[2] + (c2[2] - c1[2]) * y / h)
        d.line([(0, y), (w, y)], fill=(r, g, b, 255))
    img = img.filter(ImageFilter.GaussianBlur(6))
    return img


# =========================================================
# PREMIUM IMAGE GENERATOR
# =========================================================

def make_premium(lines, theme_type="morning", profile_bytes=None, username="", date_str=""):
    W, H = 1280, 720
    
    if theme_type == "morning":
        themes = MORNING_THEMES
    elif theme_type == "afternoon":
        themes = AFTERNOON_THEMES
    else:
        themes = NIGHT_THEMES
    
    theme = random.choice(themes)
    acc = theme["acc"]

    # Base gradient
    img = premium_bg(W, H, theme)
    star_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_stars(ImageDraw.Draw(star_layer), W, H, acc, count=80)
    img = Image.alpha_composite(img, star_layer)

    # Dark glass overlay
    glass = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass)
    gd.rounded_rectangle([60, 60, W - 60, H - 60], radius=30, fill=(0, 0, 0, 100))
    img = Image.alpha_composite(img, glass)

    # Accent border line at top
    border = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle([60, 60, W - 60, 65], radius=10, fill=(*acc, 200))
    img = Image.alpha_composite(img, border)

    d = ImageDraw.Draw(img)

    # Profile photo circle (left side)
    has_photo = False
    if profile_bytes:
        try:
            pimg = Image.open(io.BytesIO(profile_bytes))
            circ = circle_crop(pimg, size=170)
            # White ring
            ring = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
            ImageDraw.Draw(ring).ellipse([0, 0, 180, 180], fill=(*acc, 220))
            img.paste(ring, (110, 270), ring)
            img.paste(circ, (115, 275), circ)
            has_photo = True
        except Exception:
            pass

    # Text area — shift right if photo present
    text_x_offset = 320 if has_photo else 0
    text_center = (W + text_x_offset) // 2

    # Main lines
    y = 180
    f_big  = font(80)
    f_mid  = font(46)
    f_name = font(52)
    f_small= font(28, bold=False)

    for i, line in enumerate(lines):
        f = f_big if i == 0 else f_mid
        box = d.textbbox((0, 0), line, font=f)
        tw = box[2] - box[0]
        x = text_center - tw // 2
        # Shadow
        d.text((x + 3, y + 3), line, font=f, fill=(0, 0, 0, 160))
        # Main text
        d.text((x, y), line, font=f, fill=(255, 255, 255, 255))
        y += 100

    # Username (convert to smallcaps for stylish look)
    if username:
        username_stylish = to_smallcaps(username)
        uname_line = f"❤️  {username_stylish}"
        box = d.textbbox((0, 0), uname_line, font=f_name)
        tw = box[2] - box[0]
        x = text_center - tw // 2
        d.text((x + 2, y + 2), uname_line, font=f_name, fill=(*acc, 180))
        d.text((x, y), uname_line, font=f_name, fill=(255, 255, 255, 255))
        y += 80

    # Date / time (convert to smallcaps)
    if date_str:
        date_stylish = to_smallcaps(date_str)
        box = d.textbbox((0, 0), date_stylish, font=f_small)
        tw = box[2] - box[0]
        x = text_center - tw // 2
        d.text((x, y), date_stylish, font=f_small, fill=(*acc, 200))

    # Bot watermark bottom-right
    wm = f"✦ {to_smallcaps(BOT_NAME)}"
    box = d.textbbox((0, 0), wm, font=font(26, bold=False))
    d.text((W - (box[2] - box[0]) - 80, H - 70), wm, font=font(26, bold=False), fill=(255, 255, 255, 130))

    # Premium badge bottom-left
    badge = to_smallcaps("⭐ Premium")
    d.text((90, H - 70), badge, font=font(26), fill=(*acc, 180))

    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=96)
    buf.seek(0)
    return buf.read()


# =========================================================
# FETCH PROFILE PHOTO
# =========================================================

async def get_profile_bytes(client, user_id):
    try:
        photos = [p async for p in client.get_chat_photos(user_id, limit=1)]
        if not photos:
            return None
        buf = io.BytesIO()
        await client.download_media(photos[0].file_id, file_name=buf)
        buf.seek(0)
        return buf.read()
    except Exception:
        return None


# =========================================================
# SEND PREMIUM WITH GENDER DETECTION
# =========================================================

async def send_premium_with_gender(client, message, gender, time_period, is_wrong_time=False, wrong_text=None):
    """Send premium greeting based on gender and time period"""
    
    user = message.from_user
    username = html.escape(user.first_name if user else "User")
    
    # Select appropriate lines based on gender and time period
    if not is_wrong_time:
        if time_period == "morning":
            if gender == "girl":
                lines = random.choice(GIRL_MORNING_LINES)
                gender_emoji = "🌸"
            elif gender == "boy":
                lines = random.choice(BOY_MORNING_LINES)
                gender_emoji = "💪"
            else:
                lines = random.choice(GOOD_MORNING_LINES)
                gender_emoji = "✨"
            caption = f"{lines[0]}\n\n{gender_emoji} <b>{username}</b>\n\n<i>{lines[1]}</i>"
            theme_type = "morning"
            
        elif time_period == "afternoon":
            if gender == "girl":
                lines = random.choice(GIRL_AFTERNOON_LINES)
                gender_emoji = "🌸"
            elif gender == "boy":
                lines = random.choice(BOY_AFTERNOON_LINES)
                gender_emoji = "💪"
            else:
                lines = random.choice(GOOD_AFTERNOON_LINES)
                gender_emoji = "✨"
            caption = f"{lines[0]}\n\n{gender_emoji} <b>{username}</b>\n\n<i>{lines[1]}</i>"
            theme_type = "afternoon"
            
        else:  # night
            if gender == "girl":
                lines = random.choice(GIRL_NIGHT_LINES)
                gender_emoji = "🌙"
            elif gender == "boy":
                lines = random.choice(BOY_NIGHT_LINES)
                gender_emoji = "💪"
            else:
                lines = random.choice(GOOD_NIGHT_LINES)
                gender_emoji = "✨"
            caption = f"{lines[0]}\n\n{gender_emoji} <b>{username}</b>\n\n<i>{lines[1]}</i>"
            theme_type = "night"
    else:
        # Wrong time case
        lines = [wrong_text]
        if time_period == "morning":
            caption = f"😂 <b>ᴡʀᴏɴɢ ᴛɪᴍᴇ!</b>\n\n{wrong_text}"
            theme_type = "morning"
        elif time_period == "afternoon":
            caption = f"😂 <b>ᴡʀᴏɴɢ ᴛɪᴍᴇ!</b>\n\n{wrong_text}"
            theme_type = "afternoon"
        else:
            caption = f"🤣 <b>ᴡʀᴏɴɢ ᴛɪᴍᴇ!</b>\n\n{wrong_text}"
            theme_type = "night"
    
    now = datetime.datetime.now(ZoneInfo(TIMEZONE))
    date_str = now.strftime("%d %B %Y  |  %I:%M %p")
    
    # Fetch profile photo
    profile_bytes = None
    if user:
        profile_bytes = await get_profile_bytes(client, user.id)
    
    img_bytes = await asyncio.to_thread(
        make_premium, lines, theme_type, profile_bytes, username, date_str
    )
    
    photo = io.BytesIO(img_bytes)
    photo.name = "greeting.jpg"
    
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("♪ ᴍᴜsɪᴄ ʙᴏᴛ", url=f"https://t.me/{app.username}" if app.username else SUPPORT_CHAT),
            InlineKeyboardButton("💬 sᴜᴘᴘᴏʀᴛ", url=SUPPORT_CHAT),
        ]
    ])
    
    # Convert caption to smallcaps
    caption_lines = caption.split('\n')
    caption_stylish = '\n'.join(to_smallcaps(line) if not line.startswith('☀️') and not line.startswith('🌙') and not line.startswith('🌸') and not line.startswith('💪') and not line.startswith('✨') and not line.startswith('😂') and not line.startswith('🤣') else line for line in caption_lines)
    
    await message.reply_photo(
        photo,
        caption=caption_stylish,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=kb,
    )


# =========================================================
# MESSAGE HANDLER
# =========================================================

@app.on_message(
    filters.text
    & ~filters.regex(r"^/")
    & ~filters.via_bot
    & ~filters.forwarded
    & ~BANNED_USERS,
    group=15,
)
async def greet_handler(client, message: Message):
    if not message.text:
        return

    text = message.text.strip()
    if len(text) > 80:
        return

    gm = bool(GM.search(text))
    ga = bool(GA.search(text))
    gn = bool(GN.search(text))

    if not gm and not ga and not gn:
        return

    now = message.date.astimezone(ZoneInfo(TIMEZONE))
    
    # Detect gender from username
    user = message.from_user
    if user and user.first_name:
        gender = detect_gender(user.first_name)
    else:
        gender = "neutral"

    # GOOD MORNING
    if gm:
        if is_morning(now) or ALLOW_OUT_OF_TIME_REPLY:
            await send_premium_with_gender(client, message, gender, "morning")
        else:
            wrong_text = random.choice(WRONG_MORNING)
            await send_premium_with_gender(client, message, gender, "morning", is_wrong_time=True, wrong_text=wrong_text)

    # GOOD AFTERNOON
    elif ga:
        if is_afternoon(now) or ALLOW_OUT_OF_TIME_REPLY:
            await send_premium_with_gender(client, message, gender, "afternoon")
        else:
            wrong_text = random.choice(WRONG_AFTERNOON)
            await send_premium_with_gender(client, message, gender, "afternoon", is_wrong_time=True, wrong_text=wrong_text)

    # GOOD NIGHT
    elif gn:
        if is_night(now) or ALLOW_OUT_OF_TIME_REPLY:
            await send_premium_with_gender(client, message, gender, "night")
        else:
            wrong_text = random.choice(WRONG_NIGHT)
            await send_premium_with_gender(client, message, gender, "night", is_wrong_time=True, wrong_text=wrong_text)


# =========================================================
# COMMANDS (manual trigger — always work)
# =========================================================

@app.on_message(filters.command("goodmorning") & ~BANNED_USERS)
async def gm_cmd(client, message: Message):
    user = message.from_user
    if user and user.first_name:
        gender = detect_gender(user.first_name)
    else:
        gender = "neutral"
    await send_premium_with_gender(client, message, gender, "morning")

@app.on_message(filters.command("goodafternoon") & ~BANNED_USERS)
async def ga_cmd(client, message: Message):
    user = message.from_user
    if user and user.first_name:
        gender = detect_gender(user.first_name)
    else:
        gender = "neutral"
    await send_premium_with_gender(client, message, gender, "afternoon")

@app.on_message(filters.command("goodnight") & ~BANNED_USERS)
async def gn_cmd(client, message: Message):
    user = message.from_user
    if user and user.first_name:
        gender = detect_gender(user.first_name)
    else:
        gender = "neutral"
    await send_premium_with_gender(client, message, gender, "night")
