import logging
import math
from datetime import date
from django.conf import settings
from django.template.loader import get_template
from asgiref.sync import sync_to_async
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from nhl_data.models import Game
from .services import TelegramUserService

logger = logging.getLogger(__name__)


async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Register or update user information in the database.
    This function should be called for every user interaction.
    """
    try:
        user = update.effective_user
        if user:
            # Use sync_to_async to handle the database operation
            await sync_to_async(TelegramUserService.get_or_create_user)(user)
            logger.info(f"User {user.id} registered/updated successfully")
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /start is issued."""
    # Register the user first
    await register_user(update, context)
    
    template = get_template('telegram_bot/start.txt')
    message = template.render()
    await update.message.reply_text(message)


async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a list of future NHL games for the current date."""
    # Register the user first
    await register_user(update, context)
    
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


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows a list of saved users with pagination support."""
    # Register the user first
    await register_user(update, context)
    
    try:
        # Get page number from command arguments (default to 1)
        page = 1
        if context.args and context.args[0].isdigit():
            page = int(context.args[0])
        
        # Ensure page is at least 1
        page = max(1, page)
        
        # Get users list and stats
        users_list, total_users = await sync_to_async(TelegramUserService.get_users_list)(page, 20)
        stats = await sync_to_async(TelegramUserService.get_user_stats)()
        
        if not users_list and page == 1:
            # No users found and it's the first page
            template = get_template('telegram_bot/users_empty.txt')
            message = template.render()
        else:
            # Calculate pagination info
            page_size = 20
            total_pages = math.ceil(total_users / page_size) if total_users > 0 else 1
            next_page = page + 1 if page < total_pages else None
            
            # Use users template with context
            template = get_template('telegram_bot/users.txt')
            message = template.render({
                'users': users_list,
                'total_users': stats['total_users'],
                'active_users': stats['active_users_30d'],
                'premium_users': stats['premium_users'],
                'verified_users': stats['verified_users'],
                'current_page': page,
                'total_pages': total_pages,
                'next_page': next_page,
            })
        
        await update.message.reply_text(message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in users command: {str(e)}")
        await update.message.reply_text("❌ Error retrieving users list. Please try again later.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all incoming messages and register users."""
    # Register the user for any message interaction
    await register_user(update, context)
    
    # You can add additional message handling logic here
    # For now, we'll just log that we received a message
    logger.info(f"Received message from user {update.effective_user.id}: {update.message.text[:50]}...")


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("schedule", schedule))
    application.add_handler(CommandHandler("users", users))
    
    # Handle all other messages (this will register users for any interaction)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()
