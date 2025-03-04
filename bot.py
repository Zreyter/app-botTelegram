import logging
import re
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters
import yt_dlp

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Expresión regular para detectar enlaces de Facebook
facebook_url_pattern = re.compile(r"(https?://(?:www\.)?facebook\.com/.+)", re.IGNORECASE)

# Diccionario para rastrear estados de usuarios
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hola {user.mention_html()}! Usa el menú para interactuar con el bot.",
    )

    # Menú desplegable
    keyboard = [
        [InlineKeyboardButton("Descargar Video", callback_data="descargar_video")],
        [InlineKeyboardButton("Ayuda", callback_data="ayuda")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Selecciona una opción:", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide help information."""
    await update.message.reply_text("Selecciona 'Descargar Video' del menú y envía un enlace de Facebook para descargarlo.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle menu selection."""
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    if query.data == "descargar_video":
        # Cambia el estado del usuario y pide el enlace
        user_states[user_id] = "waiting_for_url"
        await query.edit_message_text("Por favor, envíame el enlace del video de Facebook que deseas descargar.")
    elif query.data == "ayuda":
        await query.edit_message_text("Usa la opción 'Descargar Video' y envía un enlace válido de Facebook.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user input."""
    user_id = update.effective_user.id

    # Verifica si el usuario está en el estado correcto
    if user_id in user_states and user_states[user_id] == "waiting_for_url":
        url = update.message.text.strip()

        if not facebook_url_pattern.match(url):
            await update.message.reply_text("El enlace proporcionado no es válido. Por favor, envíame un enlace de video de Facebook.")
            return

        await update.message.reply_text("Descargando el video, por favor espera...")

        try:
            # Configurar yt-dlp para descargar el video
            ydl_opts = {
                "outtmpl": "video.mp4",  # Guardar como video.mp4 temporalmente
                "quiet": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Enviar el video al usuario
            with open("video.mp4", "rb") as video_file:
                await update.message.reply_video(video=video_file)

            # Eliminar el archivo temporal
            os.remove("video.mp4")

        except Exception as e:
            logger.error(f"Error al descargar el video: {e}")
            await update.message.reply_text("Hubo un error al descargar el video. Por favor, intenta nuevamente.")

        # Restablece el estado del usuario
        user_states.pop(user_id, None)
    else:
        await update.message.reply_text("No entiendo tu mensaje. Usa el menú para interactuar con el bot.")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token("8033049294:AAETZSDet8zE8ahWY2E3j8xckY556Zv0lqU").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
