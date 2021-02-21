import os
import subprocess
import sys
from time import sleep

from MeguRobot import dispatcher
from MeguRobot.modules.helper_funcs.chat_status import dev_plus
from telegram import TelegramError, Update
from telegram.ext import CallbackContext, CommandHandler


@dev_plus
def leave(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if args:
        chat_id = str(args[0])
        try:
            bot.leave_chat(int(chat_id))
            update.effective_message.reply_text("Beep boop, dejé ese grupo!.")
        except TelegramError:
            update.effective_message.reply_text(
                "Beep boop, no pude dejar ese grupo (no sé por qué)."
            )
    else:
        update.effective_message.reply_text("Envíame un ID de chat válido")


LEAVE_HANDLER = CommandHandler("leave", leave, run_async=True)

dispatcher.add_handler(LEAVE_HANDLER)

__mod_name__ = "Dev"
__handlers__ = [LEAVE_HANDLER]
