from django.core.management.base import BaseCommand
from telegram_bot import bot

class Command(BaseCommand):
    help = "Starts the Telegram bot"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Bot is starting...'))
        bot.main()