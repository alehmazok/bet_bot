"""
Services for handling Telegram user operations.
"""
import logging
from typing import Optional, Tuple, List
from django.db import transaction
from django.utils import timezone
from telegram import User as TelegramUser
from .models import TelegramUser as TelegramUserModel

logger = logging.getLogger(__name__)


class TelegramUserService:
    """Service class for managing Telegram users in the database."""
    
    @staticmethod
    def get_or_create_user(telegram_user: TelegramUser) -> Tuple[TelegramUserModel, bool]:
        """
        Get or create a Telegram user in the database.
        
        Args:
            telegram_user: The Telegram User object from the bot API
            
        Returns:
            Tuple of (TelegramUserModel instance, created boolean)
        """
        try:
            with transaction.atomic():
                # Try to get existing user
                user, created = TelegramUserModel.objects.get_or_create(
                    telegram_id=telegram_user.id,
                    defaults={
                        'first_name': telegram_user.first_name,
                        'last_name': telegram_user.last_name,
                        'username': telegram_user.username,
                    }
                )
                
                # If user exists, update their information
                if not created:
                    updated = False
                    
                    # Update basic info if changed
                    if user.first_name != telegram_user.first_name:
                        user.first_name = telegram_user.first_name
                        updated = True
                    
                    if user.last_name != telegram_user.last_name:
                        user.last_name = telegram_user.last_name
                        updated = True
                    
                    if user.username != telegram_user.username:
                        user.username = telegram_user.username
                        updated = True
                    
                    if updated:
                        user.save()
                    
                    # Always update last_seen
                    user.update_last_seen()
                
                logger.info(f"User {'created' if created else 'updated'}: {user}")
                return user, created
                
        except Exception as e:
            logger.error(f"Error getting/creating user {telegram_user.id}: {str(e)}")
            raise
    
    @staticmethod
    def get_user_by_telegram_id(telegram_id: int) -> Optional[TelegramUserModel]:
        """
        Get a user by their Telegram ID.
        
        Args:
            telegram_id: The Telegram user ID
            
        Returns:
            TelegramUserModel instance or None if not found
        """
        try:
            return TelegramUserModel.objects.get(telegram_id=telegram_id)
        except TelegramUserModel.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting user by telegram_id {telegram_id}: {str(e)}")
            raise
    
    @staticmethod
    def update_user_last_seen(telegram_id: int) -> bool:
        """
        Update the last_seen timestamp for a user.
        
        Args:
            telegram_id: The Telegram user ID
            
        Returns:
            True if user was found and updated, False otherwise
        """
        try:
            user = TelegramUserService.get_user_by_telegram_id(telegram_id)
            if user:
                user.update_last_seen()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating last_seen for user {telegram_id}: {str(e)}")
            return False
    
    @staticmethod
    def get_user_stats() -> dict:
        """
        Get basic statistics about stored users.
        
        Returns:
            Dictionary with user statistics
        """
        try:
            total_users = TelegramUserModel.objects.count()
            active_users = TelegramUserModel.objects.filter(
                last_seen__gte=timezone.now() - timezone.timedelta(days=30)
            ).count()
            
            return {
                'total_users': total_users,
                'active_users_30d': active_users,
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {
                'total_users': 0,
                'active_users_30d': 0,
            }
    
    @staticmethod
    def get_users_list(page: int = 1, page_size: int = 20) -> Tuple[List[TelegramUserModel], int]:
        """
        Get a paginated list of users.
        
        Args:
            page: Page number (1-based)
            page_size: Number of users per page
            
        Returns:
            Tuple of (list of users, total count)
        """
        try:
            offset = (page - 1) * page_size
            users = list(TelegramUserModel.objects.all().order_by('-created_at')[offset:offset + page_size])
            total_count = TelegramUserModel.objects.count()
            
            return users, total_count
        except Exception as e:
            logger.error(f"Error getting users list: {str(e)}")
            return [], 0
          