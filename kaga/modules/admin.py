"""This special for you lazy admeme"""

import html
import os

from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.utils.helpers import mention_html

from kaga import dispatcher
from kaga.modules.connection import connected
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.helper_funcs.admin_rights import (
    user_can_changeinfo,
    user_can_pin,
    user_can_promote,
)
from kaga.modules.helper_funcs.alternate import typing_action
from kaga.modules.helper_funcs.chat_status import (
    bot_admin,
    can_pin,
    can_promote,
    user_admin,
    ADMIN_CACHE,
)
from kaga.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from kaga.modules.log_channel import loggable


@bot_admin
@can_promote
@user_admin
@loggable
@typing_action
def promote(update, context):
    chat_id = update.effective_chat.id
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if user_can_promote(chat, user, context.bot.id) is False:
        message.reply_text("Anda tidak memiliki cukup hak untuk mempromosikan seseorang!")
        return ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("mention one.... 🤷🏻‍♂.")
        return ""

    user_member = chat.get_member(user_id)
    if (
        user_member.status == "administrator"
        or user_member.status == "creator"
    ):
        message.reply_text("Orang ini sudah menjadi admin...!")
        return ""

    if user_id == context.bot.id:
        message.reply_text("Saya berharap, jika saya bisa mempromosikan diri saya sendiri!")
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(context.bot.id)

    context.bot.promoteChatMember(
        chat_id,
        user_id,
        can_change_info=bot_member.can_change_info,
        can_post_messages=bot_member.can_post_messages,
        can_edit_messages=bot_member.can_edit_messages,
        can_delete_messages=bot_member.can_delete_messages,
        can_invite_users=bot_member.can_invite_users,
        can_restrict_members=bot_member.can_restrict_members,
        can_pin_messages=bot_member.can_pin_messages,
    )

    message.reply_text("Promoted🧡")
    return (
        "<b>{}:</b>"
        "\n#PROMOTED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {}".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(user_member.user.id, user_member.user.first_name),
        )
    )


@bot_admin
@can_promote
@user_admin
@loggable
@typing_action
def demote(update, context):
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if user_can_promote(chat, user, context.bot.id) is False:
        message.reply_text("Anda tidak memiliki cukup hak untuk menurunkan seseorang!")
        return ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("mention one.... 🤷🏻‍♂.")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == "creator":
        message.reply_text("Saya tidak akan menurunkan Kreator dari grup ini.... 🙄")
        return ""

    if not user_member.status == "administrator":
        message.reply_text(
            "Bagaimana saya bisa menurunkan seseorang yang bahkan bukan admin!"
        )
        return ""

    if user_id == context.bot.id:
        message.reply_text("Yah ... Tidak akan menurunkan diriku sendiri!")
        return ""

    try:
        context.bot.promoteChatMember(
            int(chat.id),
            int(user_id),
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
        )
        message.reply_text("Berhasil diturunkan!")
        return (
            "<b>{}:</b>"
            "\n#DEMOTED"
            "\n<b>Admin:</b> {}"
            "\n<b>Pengguna:</b> {}".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                mention_html(user_member.user.id, user_member.user.first_name),
            )
        )

    except BadRequest:
        message.reply_text(
            "Gagal menurunkan. Saya mungkin bukan admin, atau status admin diangkat oleh orang lain "
            "pengguna, jadi saya tidak bisa menindaklanjutinya!"
        )
        return ""


@bot_admin
@can_pin
@user_admin
@loggable
@typing_action
def pin(update, context):
    args = context.args
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message

    is_group = chat.type != "private" and chat.type != "channel"

    prev_message = update.effective_message.reply_to_message

    if user_can_pin(chat, user, context.bot.id) is False:
        message.reply_text("Anda kehilangan hak untuk menyematkan pesan!")
        return ""

    is_silent = True
    if len(args) >= 1:
        is_silent = not (
            args[0].lower() == "notify"
            or args[0].lower() == "loud"
            or args[0].lower() == "violent"
        )

    if prev_message and is_group:
        try:
            context.bot.pinChatMessage(
                chat.id,
                prev_message.message_id,
                disable_notification=is_silent,
            )
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        return (
            "<b>{}:</b>"
            "\n#PINNED"
            "\n<b>Admin:</b> {}".format(
                html.escape(chat.title), mention_html(user.id, user.first_name)
            )
        )

    return ""


@bot_admin
@can_pin
@user_admin
@loggable
@typing_action
def unpin(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if user_can_pin(chat, user, context.bot.id) is False:
        message.reply_text("Anda kehilangan hak untuk melepas pin pada pesan!")
        return ""

    try:
        context.bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        elif excp.message == "Message to unpin not found":
            message.reply_text(
                "Saya tidak dapat melihat pesan yang dipasangi pin, Mungkin sudah tidak terhubung, atau sematkan ke Pesan lama 🙂"
            )
        else:
            raise

    return (
        "<b>{}:</b>"
        "\n#UNPINNED"
        "\n<b>Admin:</b> {}".format(
            html.escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@bot_admin
@user_admin
@typing_action
def invite(update, context):
    user = update.effective_user
    msg = update.effective_message
    chat = update.effective_chat
    context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
    else:
        if msg.chat.type == "private":
            msg.reply_text("Perintah ini dimaksudkan untuk digunakan dalam obrolan bukan di PM")
            return ""
        chat = update.effective_chat

    if chat.username:
        msg.reply_text(chat.username)
    elif chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        bot_member = chat.get_member(context.bot.id)
        if bot_member.can_invite_users:
            invitelink = context.bot.exportChatInviteLink(chat.id)
            msg.reply_text(invitelink)
        else:
            msg.reply_text(
                "Saya tidak memiliki akses ke tautan undangan, coba ubah izin saya!"
            )
    else:
        msg.reply_text(
            "Saya hanya dapat memberi Anda tautan undangan untuk supergrup dan saluran, maaf!"
        )


@typing_action
def adminlist(update, context):
    administrators = update.effective_chat.get_administrators()
    text = "Admins in <b>{}</b>:".format(
        update.effective_chat.title or "this chat"
    )
    for admin in administrators:
        user = admin.user
        status = admin.status
        name = f"{(mention_html(user.id, user.first_name))}"
        if status == "creator":
            text += "\n 🦁 Creator:"
            text += "\n • {} \n\n 🦊 Admin:".format(name)
    for admin in administrators:
        user = admin.user
        status = admin.status
        name = f"{(mention_html(user.id, user.first_name))}"
        if status == "administrator":
            text += "\n • {}".format(name)
    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@bot_admin
@can_promote
@user_admin
@typing_action
def set_title(update, context):
    args = context.args
    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except Exception:
        return

    if not user_id:
        message.reply_text("Anda sepertinya tidak mengacu pada pengguna.")
        return

    if user_member.status == "creator":
        message.reply_text(
            "Orang ini MENCIPTAKAN obrolan, bagaimana saya bisa mengatur title khusus untuknya?"
        )
        return

    if not user_member.status == "administrator":
        message.reply_text(
            "Tidak dapat menyetel title untuk non-admin!\nPromosikan mereka terlebih dahulu untuk menyetel title kustom!"
        )
        return

    if user_id == context.bot.id:
        message.reply_text(
            "Saya tidak dapat menetapkan title saya sendiri! Dapatkan orang yang menjadikan saya admin untuk melakukannya untuk saya."
        )
        return

    if not title:
        message.reply_text("Menyetel title kosong tidak akan menghasilkan apa-apa!")
        return

    if len(title) > 16:
        message.reply_text(
            "Panjang title lebih dari 16 karakter.\nMemotongnya menjadi 16 karakter."
        )

    try:
        context.bot.set_chat_administrator_custom_title(
            chat.id, user_id, title
        )
        message.reply_text(
            "Berhasil menetapkan title untuk <b>{}</b> ke <code>{}</code>!".format(
                user_member.user.first_name or user_id, title[:16]
            ),
            parse_mode=ParseMode.HTML,
        )

    except BadRequest:
        message.reply_text(
            "Saya tidak dapat menyetel title khusus untuk admin yang tidak saya promosikan!"
        )


@bot_admin
@user_admin
@typing_action
def setchatpic(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Anda kehilangan hak untuk mengubah info grup!")
        return

    if msg.reply_to_message:
        if msg.reply_to_message.photo:
            pic_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            pic_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("Anda hanya dapat mengatur beberapa foto sebagai gambar obrolan!")
            return
        dlmsg = msg.reply_text("Tunggu sebentar...")
        tpic = context.bot.get_file(pic_id)
        tpic.download("gpic.png")
        try:
            with open("gpic.png", "rb") as chatp:
                context.bot.set_chat_photo(int(chat.id), photo=chatp)
                msg.reply_text("Berhasil menyetel gambar grup baru!")
        except BadRequest as excp:
            msg.reply_text(f"Error! {excp.message}")
        finally:
            dlmsg.delete()
            if os.path.isfile("gpic.png"):
                os.remove("gpic.png")
    else:
        msg.reply_text("Balas beberapa foto atau file untuk menyetel gambar obrolan baru!")


@bot_admin
@user_admin
@typing_action
def rmchatpic(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Anda tidak memiliki cukup hak untuk menghapus foto grup")
        return
    try:
        context.bot.delete_chat_photo(int(chat.id))
        msg.reply_text("Successfully deleted chat's profile photo!")
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")
        return


@bot_admin
@user_admin
@typing_action
def setchat_title(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    args = context.args

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Anda tidak memiliki cukup hak untuk mengubah info obrolan!")
        return

    title = " ".join(args)
    if not title:
        msg.reply_text("Masukkan beberapa teks untuk menyetel judul baru dalam obrolan Anda!")
        return

    try:
        context.bot.set_chat_title(int(chat.id), str(title))
        msg.reply_text(
            f"Berhasil disetel <b>{title}</b> sebagai judul obrolan baru!",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")
        return


@bot_admin
@user_admin
@typing_action
def set_sticker(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text("Anda kehilangan hak untuk mengubah info obrolan!")

    if msg.reply_to_message:
        if not msg.reply_to_message.sticker:
            return msg.reply_text(
                "Anda perlu membalas beberapa stiker untuk menyetel kumpulan stiker obrolan!"
            )
        stkr = msg.reply_to_message.sticker.set_name
        try:
            context.bot.set_chat_sticker_set(chat.id, stkr)
            msg.reply_text(
                f"Berhasil menyetel stiker grup baru in {chat.title}!"
            )
        except BadRequest as excp:
            if excp.message == "Participants_too_few":
                return msg.reply_text(
                    "Maaf, karena pembatasan telegram, obrolan harus memiliki minimal 100 anggota sebelum mereka dapat memiliki stiker grup!"
                )
            msg.reply_text(f"Error! {excp.message}.")
    else:
        msg.reply_text(
            "Anda perlu membalas beberapa stiker untuk menyetel kumpulan stiker obrolan!"
        )


@bot_admin
@user_admin
@typing_action
def set_desc(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text("Anda kehilangan hak untuk mengubah info obrolan!")

    tesc = msg.text.split(None, 1)
    if len(tesc) >= 2:
        desc = tesc[1]
    else:
        return msg.reply_text("Menyetel deskripsi kosong tidak akan melakukan apa pun!")
    try:
        if len(desc) > 255:
            return msg.reply_text(
                "Deskripsi harus kurang dari 255 karakter!"
            )
        context.bot.set_chat_description(chat.id, desc)
        msg.reply_text(
            f"Deskripsi obrolan berhasil diperbarui dalam {chat.title}!"
        )
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")


@user_admin
@typing_action
def refresh_admin(update, _):
    try:
        ADMIN_CACHE.pop(update.effective_chat.id)
    except KeyError:
        pass

    update.effective_message.reply_text("Cache admin disegarkan!")


def __chat_settings__(chat_id, user_id):
    return "You are *admin*: `{}`".format(
        dispatcher.bot.get_chat_member(chat_id, user_id).status
        in ("administrator", "creator")
    )


__help__ = """
Malas mempromosikan atau menurunkan seseorang sebagai admin? Ingin melihat informasi dasar tentang obrolan? \
Semua hal tentang ruang obrolan seperti daftar admin, menyematkan atau mengambil tautan undangan bisa\
dilakukan dengan mudah menggunakan bot.

 × /adminlist: daftar admin dalam obrolan

*Khusus Admin:*
 × /pin: Pin diam-diam pesan yang dibalas - add `loud`, `notify` atau `violent` untuk memberikan pemberitahuan kepada pengguna.
 × /unpin: Lepas pin pesan yang saat ini disematkan.
 × /invitelink: Mendapat tautan masuk obrolan pribadi.
 × /promote: Mempromosikan pengguna membalas.
 × /demote: Mempromosikan pengguna membalas.
 × /settitle: Menetapkan title khusus untuk admin yang dipromosikan oleh bot.
 × /setgpic: Sebagai balasan untuk file atau foto untuk mengatur foto profil grup!
 × /delgpic: Sama seperti di atas tetapi untuk menghapus foto profil grup.
 × /setgtitle <newtitle>: Tetapkan title obrolan baru di grup Anda.
 × /setsticker: Sebagai balasan untuk beberapa stiker untuk mengaturnya sebagai set stiker grup!
 × /setdescription: <description> Tetapkan deskripsi obrolan baru dalam grup.

*Catatan*: Untuk mengatur obrolan set stiker grup harus memiliki minimal 100 anggota. 554

Contoh mempromosikan seseorang menjadi admin:
`/promote @username`;ni mempromosikan pengguna menjadi admin.
"""

__mod_name__ = "Admin"

PIN_HANDLER = CommandHandler(
    "pin", pin, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
UNPIN_HANDLER = CommandHandler(
    "unpin", unpin, filters=Filters.chat_type.groups, run_async=True
)
INVITE_HANDLER = CommandHandler("invitelink", invite, run_async=True)
CHAT_PIC_HANDLER = CommandHandler(
    "setgpic", setchatpic, filters=Filters.chat_type.groups, run_async=True
)
DEL_CHAT_PIC_HANDLER = CommandHandler(
    "delgpic", rmchatpic, filters=Filters.chat_type.groups, run_async=True
)
SETCHAT_TITLE_HANDLER = CommandHandler(
    "setgtitle", setchat_title, filters=Filters.chat_type.groups, run_async=True
)
SETSTICKET_HANDLER = CommandHandler(
    "setsticker", set_sticker, filters=Filters.chat_type.groups, run_async=True
)
SETDESC_HANDLER = CommandHandler(
    "setdescription", set_desc, filters=Filters.chat_type.groups, run_async=True
)

PROMOTE_HANDLER = CommandHandler(
    "promote", promote, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
DEMOTE_HANDLER = CommandHandler(
    "demote", demote, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)

SET_TITLE_HANDLER = DisableAbleCommandHandler(
    "settitle", set_title, pass_args=True, run_async=True
)
ADMINLIST_HANDLER = DisableAbleCommandHandler(
    "adminlist", adminlist, filters=Filters.chat_type.groups, run_async=True
)
ADMIN_REFRESH_HANDLER = CommandHandler(
    "admincache", refresh_admin, run_async=True
)


dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(ADMIN_REFRESH_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)
dispatcher.add_handler(CHAT_PIC_HANDLER)
dispatcher.add_handler(DEL_CHAT_PIC_HANDLER)
dispatcher.add_handler(SETCHAT_TITLE_HANDLER)
dispatcher.add_handler(SETSTICKET_HANDLER)
dispatcher.add_handler(SETDESC_HANDLER)
