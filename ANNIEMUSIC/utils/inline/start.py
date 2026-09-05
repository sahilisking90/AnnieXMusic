from pyrogram.types import InlineKeyboardButton

import config
from ANNIEMUSIC import app

# ── Premium Emoji IDs (from your registry scan) ───────────────────────────
# Assign the 18 found IDs to semantic roles so every button gets one.
_PE = {
    "add":      5467641505525016018,   # ⭐  — Add to Group
    "channel":  6197411888553270114,   # ⭐  — Channel
    "help":     6122805733936342496,   # ⭐  — Help Center
    "support":  6183633702187176982,   # ⭐  — Support Chat
    "owner":    5193037303961920951,   # ⭐  — Owner
    "youtube":  6035239240625820254,   # ⭐  — YouTube link
    "back":     6091402470666279677,   # ⭐  — Back
    "star1":    5348227245599105972,
    "star2":    6305370152145787193,
    "star3":    5890937706803894250,
    "star4":    5310095671246733180,
    "star5":    5301276827782755360,
    "star6":    5292226786229236118,
    "star7":    6292050745596315294,
    "star8":    6203911118964924015,
    "star9":    5326049357332513437,
    "star10":   5355051922862653659,
    "star11":   6118385795976930086,
}


def _pe_tag(emoji_id: int, fallback: str) -> str:
    """Wrap a premium emoji document ID into a tg-emoji HTML tag."""
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


def _btn(text: str, emoji_key: str, fallback: str, **kwargs) -> InlineKeyboardButton:
    """
    Build an InlineKeyboardButton with a premium emoji prepended to the label.

    TG Bot API 9.4 style parameter values:
        style="primary"  → blue
        style="success"  → green
        style="danger"   → red
        (omit)           → default grey

    Pyrogram passes extra kwargs straight through to the Button constructor,
    so style= lands in the JSON payload as-is when Pyrogram supports it.
    Falls back cleanly on older Pyrogram builds that ignore unknown kwargs.
    """
    label = f"{_pe_tag(_PE[emoji_key], fallback)} {text}"
    return InlineKeyboardButton(text=label, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# GROUP /start  →  Add bot  +  Channel
# ─────────────────────────────────────────────────────────────────────────────
def start_panel(_):
    buttons = [
        [
            _btn(
                _["S_B_1"], "add", "➕",
                url=f"https://t.me/{app.username}?startgroup=true",
                style="primary",           # blue — main CTA
            ),
            _btn(
                _["S_B_2"], "channel", "📢",
                url=config.SUPPORT_CHANNEL,
                style="success",           # green — secondary CTA
            ),
        ],
    ]
    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# PRIVATE /start  →  Add  |  Owner + Support  |  Help Center
# ─────────────────────────────────────────────────────────────────────────────
def private_panel(_):
    buttons = [
        [
            _btn(
                _["S_B_1"], "add", "➕",
                url=f"https://t.me/{app.username}?startgroup=true",
                style="primary",           # blue — add to group
            ),
        ],
        [
            _btn(
                _["S_B_7"], "owner", "👑",
                user_id=config.OWNER_ID,
                style="success",           # green — owner profile
            ),
            _btn(
                _["S_B_4"], "support", "❄️",
                url=config.SUPPORT_CHAT,
                style="primary",           # blue — support
            ),
        ],
        [
            _btn(
                _["S_B_3"], "help", "✦",
                callback_data="open_help",
                style="success",           # green — help center
            ),
        ],
    ]
    return buttons
