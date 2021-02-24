from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters
from MeguRobot.modules.utils import custom_filters
from MeguRobot import pyrogrm, DEV_USERS

from MeguRobot.modules.whois import whois
from MeguRobot.modules.reverse import google_rs
from MeguRobot.modules.telegraph import telegraph
from MeguRobot.modules.spbinfo import lookup
from MeguRobot.modules.usage import usage
from MeguRobot.modules.whatanime import whatanime


handlers = [
    MessageHandler(whois, custom_filters.command("whois")),
    MessageHandler(telegraph, custom_filters.command("telegraph")),
    MessageHandler(google_rs, custom_filters.command("reverse")),
    MessageHandler(lookup, custom_filters.command("spbinfo")),
    MessageHandler(usage, custom_filters.command("usage") & filters.user(DEV_USERS)),
    MessageHandler(whatanime, custom_filters.command("whatanime")),
]

for handler in handlers:
    megu.add_handler(handler)
