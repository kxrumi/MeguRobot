import random
from datetime import datetime

from MeguRobot import dispatcher
from MeguRobot.modules.disable import (
    DisableAbleCommandHandler,
    DisableAbleMessageHandler,
)
from MeguRobot.modules.sql import afk_sql as sql
from MeguRobot.modules.users import get_user_id
from telegram import MessageEntity, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Filters, MessageHandler

AFK_GROUP = 7
AFK_REPLY_GROUP = 8


def afk(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    notice = ""
    if len(args) >= 2:
        reason = args[1]
        if len(reason) > 100:
            reason = reason[:100]
            notice = (
                "\nTu motivo de afk es demasiado largo, se redujo a 100 caracteres."
            )
    else:
        reason = ""

    time_start = datetime.now()
    sql.set_afk(update.effective_user.id, reason, time_start)
    fname = update.effective_user.first_name
    update.effective_message.reply_text("{} ahora está AFK!{}".format(fname, notice))


def no_longer_afk(update: Update, context: CallbackContext):
    user = update.effective_user
    message = update.effective_message

    if not user:  # ignore channels
        return

    user_sql = sql.check_afk_status(user.id)
    afk_time = get_time(user_sql)
    res = sql.rm_afk(user.id)
    if res:
        if message.new_chat_members:  # dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            options = [
                "{} esta aquí!",
                "{} a vuelto!",
                "{} está de nuevo en el chat!",
                "{} esta despierto!",
                "{} a vuelto a estar en linea!",
                "{} finalmente está aquí!",
                "Por fin volviste {}, te estábamos esperando!",
                "Bienvenido de vuelta! {}",
                "{} está en línea nuevamente ¿Quieres ver unas explosiones?💥",
                "¿Dónde está {}?\nEn el chat!",
            ]
            chosen_option = random.choice(options).format(firstname)
            output = "{}\nTiempo AFK: {}".format(chosen_option, afk_time)
            update.effective_message.reply_text(output)
        except:
            return


def reply_afk(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
    ):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
        )

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            if ent.type == MessageEntity.MENTION:
                user_id = get_user_id(
                    message.text[ent.offset : ent.offset + ent.length]
                )
                if not user_id:
                    # Should never happen, since for a user to become AFK they must have spoken. Maybe changed username?
                    return

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

                try:
                    chat = bot.get_chat(user_id)
                except BadRequest:
                    print(
                        "Error: No se pudo obtener el userid {} para el módulo AFK".format(
                            user_id
                        )
                    )
                    return
                fst_name = chat.first_name

            else:
                return

            check_afk(update, context, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(update, context, user_id, fst_name, userc_id)


def check_afk(update, context, user_id, fst_name, userc_id):
    if sql.is_afk(user_id):
        user = sql.check_afk_status(user_id)
        afk_time = get_time(user)
        if not user.reason:
            if int(userc_id) == int(user_id):
                return
            res = "{} está afk desde hace {}.".format(fst_name, afk_time)
            update.effective_message.reply_text(res)
        else:
            if int(userc_id) == int(user_id):
                return
            res = "{} está afk desde hace {}.\nRazón: \n{}".format(fst_name, afk_time, user.reason)
            update.effective_message.reply_text(res)


def get_time(user):
    afk_diff = datetime.now() - user.time_start
    seconds = afk_diff.seconds
    minutes = seconds / 60
    hours = minutes / 60
    days = afk_diff.days
    if days:
        afk_time = "{} dias y {} horas".format(days, hours)
    elif hours:
        afk_time = "{} horas y {} minutos".format(hours, minutes)
    elif minutes:
        afk_time = "{} minutos y {} segundos".format(minutes, seconds)
    else:
        afk_time = "{} segundos".format(seconds)
    return afk_time


__help__ = """
•`/afk <razón>`: Se marca como AFK (Lejos del Teclado).
•`brb <razón>`: Igual que el comando afk, pero no un comando.
Cuando se marca como AFK, cualquier mención será respondida con un mensaje para decirle que no está disponible.
"""

AFK_HANDLER = DisableAbleCommandHandler("afk", afk, run_async=True)
AFK_REGEX_HANDLER = DisableAbleMessageHandler(
    Filters.regex("(?i)brb"), afk, friendly="afk", run_async=True
)

NO_AFK_HANDLER = DisableAbleMessageHandler(
    Filters.all & Filters.chat_type.groups,
    no_longer_afk,
    friendly="afk",
)
AFK_REPLY_HANDLER = DisableAbleMessageHandler(
    (Filters.entity(MessageEntity.MENTION) | Filters.entity(MessageEntity.TEXT_MENTION))
    & Filters.chat_type.groups,
    reply_afk,
    friendly="afk",
)

dispatcher.add_handler(AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REGEX_HANDLER, AFK_GROUP)
dispatcher.add_handler(NO_AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)

__mod_name__ = "AFK"
__command_list__ = ["afk"]
__handlers__ = [
    (AFK_HANDLER, AFK_GROUP),
    (AFK_REGEX_HANDLER, AFK_GROUP),
    (NO_AFK_HANDLER, AFK_GROUP),
    (AFK_REPLY_HANDLER, AFK_REPLY_GROUP),
]
