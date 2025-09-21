import logging
from datetime import date
from django.conf import settings
from asgiref.sync import sync_to_async
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from nhl_data.models import Game

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /start is issued."""
    await update.message.reply_text("Hello! I am your bot.")


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
            await update.message.reply_text("No upcoming games scheduled.")
            return

        # Format the games list
        message_lines = [
            f"🏒 **Upcoming NHL Games - {current_date.strftime('%d.%m.%Y')}**\n"
        ]

        for i, game in enumerate(future_games):
            # Convert UTC time to a more readable format
            local_time = game.start_time_utc.strftime("%H:%M UTC")

            # Create game line
            game_line = f"**{i+1}.** {game.away_team_abbreviation} @ {game.home_team_abbreviation} - {local_time}"

            message_lines.append(game_line)

        # Join all lines and send
        message = "\n".join(message_lines)
        await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in schedule command: {str(e)}")
        await update.message.reply_text(
            "Sorry, I couldn't retrieve the schedule right now. Please try again later."
        )


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("schedule", schedule))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()
