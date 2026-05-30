"""Multilingual "hello" greetings shown on the dashboard.

A fresh one is chosen each time a user logs in or creates an account, so the
greeting rotates between sign-ins. All entries are Latin-script so they stay
readable regardless of the device's installed fonts.
"""
import random

# Each entry means roughly "hello" / "hi" / "greetings" in a different language.
HELLO_GREETINGS = [
    'Hello',        # English
    'Habari',       # Swahili
    'Jambo',        # Swahili
    'Bonjour',      # French
    'Hola',         # Spanish
    'Hallo',        # German
    'Ciao',         # Italian
    'Olá',          # Portuguese
    'Namaste',      # Hindi
    'Salaam',       # Arabic / Persian
    'Marhaba',      # Arabic
    'Konnichiwa',   # Japanese
    'Annyeong',     # Korean
    'Ni hao',       # Mandarin
    'Merhaba',      # Turkish
    'Shalom',       # Hebrew
    'Sawubona',     # Zulu
    'Privet',       # Russian
]


def pick_greeting(exclude=None):
    """Return a random greeting, avoiding `exclude` so it visibly changes."""
    choices = [g for g in HELLO_GREETINGS if g != exclude] or HELLO_GREETINGS
    return random.choice(choices)
