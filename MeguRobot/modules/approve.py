import html
from MeguRobot.modules.disable import DisableAbleCommandHandler
from MeguRobot import dispatcher, SUDO_USERS
from MeguRobot.modules.helper_funcs.extraction import extract_user
from telegram.ext import CallbackContext, CallbackQueryHandler, Filters
import MeguRobot.modules.sql.approve_sql as sql
from MeguRobot.modules.helper_funcs.chat_status import user_admin
from MeguRobot.modules.log_channel import loggable
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.utils.helpers import mention_html
from telegram.error import BadRequest


@loggable
@user_admin
def approve(update, context):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("No conozco a ese usuario!")
        return ""
    try:
        member = chat.get_member(user_id)
    except BadRequest:
        return ""
    if member.status == "administrator" or member.status == "creator":
        message.reply_text(
            "El usuario ya es administrador: los bloqueos, las listas de bloqueo y el antiflood ya no se aplican a ellos."
        )
        return ""
    if sql.is_approved(message.chat_id, user_id):
        message.reply_text(
            f"[{member.user['first_name']}](tg://user?id={member.user['id']}) ya está libre en {chat_title}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ""
    sql.approve(message.chat_id, user_id)
    message.reply_text(
        f"[{member.user['first_name']}](tg://user?id={member.user['id']}) ha sido liberado en {chat_title}. Ahora será ignorado por acciones de administración automatizadas como bloqueode la lista negra y anti-flood.",
        parse_mode=ParseMode.MARKDOWN,
    )
    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#Libre\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    return log_message


@loggable
@user_admin
def disapprove(update, context):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("No conozco a ese usuario!")
        return ""
    try:
        member = chat.get_member(user_id)
    except BadRequest:
        return ""
    if member.status == "administrator" or member.status == "creator":
        message.reply_text(
            "Este usuario es un administrador, no se puede quitar la libertad."
        )
        return ""
    if not sql.is_approved(message.chat_id, user_id):
        message.reply_text(f"{member.user['first_name']} isn't approved yet!")
        return ""
    sql.disapprove(message.chat_id, user_id)
    message.reply_text(
        f"{member.user['first_name']} is no longer approved in {chat_title}."
    )
    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#QuitaLibre\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    return log_message


@user_admin
def approved(update, context):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    msg = "Los siguientes usuarios están libres:\n"
    approved_users = sql.list_approved(message.chat_id)
    for i in approved_users:
        member = chat.get_member(int(i.user_id))
        msg += f"• [{member.user['first_name']}](tg://user?id={i.user_id})\n"
    if msg.endswith("libre.\n"):
        message.reply_text(f"No hay usuarios libres en {chat_title}:")
        return ""
    else:
        message.reply_text(
            msg,
            parse_mode=ParseMode.MARKDOWN,
        )


@user_admin
def approval(update, context):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user_id = extract_user(message, args)
    member = chat.get_member(int(user_id))
    if not user_id:
        message.reply_text("No conozco a ese usuario!")
        return ""
    if sql.is_approved(message.chat_id, user_id):
        message.reply_text(
            f"{member.user['first_name']} es un usuario libre. No se les aplicarán bloqueos, antiflood ni listas negras."
        )
    else:
        message.reply_text(
            f"{member.user['first_name']} no es un usuario libre. Se verá afectado por los comandos."
        )


def unapproveall(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        update.effective_message.reply_text(
            "Solo el propietario del chat puede quitar la libertad de todos los usuarios a la vez."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Quitar", callback_data="unapproveall_user"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Cancelar", callback_data="unapproveall_cancel"
                    )
                ],
            ]
        )
        update.effective_message.reply_text(
            f"¿Estás seguro de que deseas quitar la libertad a TODOS los usuarios en {chat.title}? Esta acción no se puede deshacer.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


def unapproveall_btn(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = update.effective_chat
    message = update.effective_message
    member = chat.get_member(query.from_user.id)
    if query.data == "unapproveall_user":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            message.edit_text("Se quitó la libertad a todos los usuarios.")
            users = []
            approved_users = sql.list_approved(chat.id)
            for i in approved_users:
                users.append(int(i.user_id))
            for user_id in users:
                sql.disapprove(chat.id, user_id)

        if member.status == "administrator":
            query.answer("Solo el propietario del chat puede hacer esto.")

        if member.status == "member":
            query.answer("Necesitas ser administrador para hacer esto.")
    elif query.data == "unapproveall_cancel":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            message.edit_text("Se canceló la eliminación de todos los usuarios libres.")
            return ""
        if member.status == "administrator":
            query.answer("Solo el propietario del chat puede hacer esto.")
        if member.status == "member":
            query.answer("Solo el propietario del chat puede hacer esto.")


__help__ = """
A veces, puede confiar en que un usuario no enviará contenido no deseado. Tal vez no sea suficiente para convertirlos en administradores, pero es posible que no se apliquen bloqueos, listas negras y antiflood a ellos. Para eso están las liberaciones: libera a usuarios confiables para permitirles enviar. 
*Comandos de administrador:*  
 •`/freestatus`: Verifica el estado de aprobación de un usuario en el chat actual.
 •`/free`: Liberar a un usuario. Los bloqueos, las listas negras y el anti-flood ya no se les aplicarán.
 •`/unfree`: Desaprobar a un usuario. Estará sujeto a bloqueos, listas negras y antiinundación nuevamente.
 •`/freelist`: Lista todos los usuarios aprobados.
  •`/unfreeall`: Quitar la libertad de *TODOS* los usuarios en un chat. Esto no se puede deshacer.
"""

APPROVE = DisableAbleCommandHandler("free", approve, filters=Filters.chat_type.groups)
DISAPPROVE = DisableAbleCommandHandler(
    "unfree", disapprove, filters=Filters.chat_type.groups, run_async=True
)
APPROVED = DisableAbleCommandHandler(
    "freelist", approved, filters=Filters.chat_type.groups, run_async=True
)
APPROVAL = DisableAbleCommandHandler(
    "freestatus", approval, filters=Filters.chat_type.groups, run_async=True
)
UNAPPROVEALL = DisableAbleCommandHandler(
    "unfreeall", unapproveall, filters=Filters.chat_type.groups, run_async=True
)
UNAPPROVEALL_BTN = CallbackQueryHandler(
    unapproveall_btn, pattern=r"unapproveall_.*", run_async=True
)

dispatcher.add_handler(APPROVE)
dispatcher.add_handler(DISAPPROVE)
dispatcher.add_handler(APPROVED)
dispatcher.add_handler(APPROVAL)
dispatcher.add_handler(UNAPPROVEALL)
dispatcher.add_handler(UNAPPROVEALL_BTN)

__mod_name__ = "Libres"
__command_list__ = ["free", "unfree", "freelist", "freestatus"]
__handlers__ = [APPROVE, DISAPPROVE, APPROVED, APPROVAL]
