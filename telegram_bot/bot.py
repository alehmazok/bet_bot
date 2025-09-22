import logging
from datetime import date
from django.conf import settings
from django.template.loader import get_template
from asgiref.sync import sync_to_async
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from nhl_data.models import Game

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /start is issued."""
    template = get_template('telegram_bot/start.txt')
    message = template.render()
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

        if not future_games:
            # Use empty schedule template
            template = get_template('telegram_bot/schedule_empty.txt')
            message = template.render()
        else:
            # Use schedule template with context
            template = get_template('telegram_bot/schedule.txt')
            message = template.render({
                'current_date': current_date.strftime('%d.%m.%Y'),
                'games': future_games
            })
        
        await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in schedule command: {str(e)}")
        template = get_template('telegram_bot/schedule_error.txt')
        error_message = template.render()
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
