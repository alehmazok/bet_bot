import logging
from datetime import date
from django.conf import settings
from asgiref.sync import sync_to_async
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from nhl_data.models import Game
from .template_loader import template_loader

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /start is issued."""
    message = template_loader.render_template("start")
    await update.message.reply_text(message)


async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a list of future NHL games for the current date."""
    try:
        # Get current date
        current_date = date.today()

        # Query for future games starting from today - wrapped in sync_to_async
        future_games = await sync_to_async(list)(
            Game.objects.filter(game_date__gte=current_date, game_state="FUT").order_by(
                "game_date", "start_time_utc"
            )[
                :10
            ]  # Limit to 10 games
        )

        # Use template loader to format the message
        message = template_loader.render_schedule_message(
            future_games, 
            current_date.strftime('%d.%m.%Y')
        )
        
        await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in schedule command: {str(e)}")
        error_message = template_loader.render_template("schedule_error")
        await update.message.reply_text(error_message)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("schedule", schedule))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()
