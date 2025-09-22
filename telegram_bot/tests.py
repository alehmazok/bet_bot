"""
Comprehensive test suite for telegram_bot app.
Covers models, services, bot handlers, templates, and admin functionality.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.template.loader import get_template
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.db import IntegrityError
from asgiref.sync import sync_to_async
from telegram import Update, User as TelegramUser, Message, Chat
from telegram.ext import ContextTypes

from .models import TelegramUser as TelegramUserModel
from .services import TelegramUserService
from .admin import TelegramUserAdmin
from .bot import start, schedule, users, handle_message, register_user


class TelegramUserModelTest(TestCase):
    """Test cases for TelegramUser model."""
    
    def setUp(self):
        """Set up test data."""
        self.test_user = TelegramUserModel.objects.create(
            telegram_id=123456789,
            first_name="John",
            last_name="Doe",
            username="johndoe"
        )
    
    def test_model_creation(self):
        """Test basic model creation."""
        self.assertEqual(self.test_user.telegram_id, 123456789)
        self.assertEqual(self.test_user.first_name, "John")
        self.assertEqual(self.test_user.last_name, "Doe")
        self.assertEqual(self.test_user.username, "johndoe")
        self.assertIsNotNone(self.test_user.created_at)
        self.assertIsNotNone(self.test_user.updated_at)
        self.assertIsNotNone(self.test_user.last_seen)
    
    def test_model_str_representation(self):
        """Test string representation of the model."""
        # Test with username
        self.assertEqual(str(self.test_user), "@johndoe (123456789)")
        
        # Test without username
        user_no_username = TelegramUserModel.objects.create(
            telegram_id=987654321,
            first_name="Jane",
            last_name="Smith"
        )
        self.assertEqual(str(user_no_username), "Jane Smith (987654321)")
        
        # Test with only first name
        user_first_only = TelegramUserModel.objects.create(
            telegram_id=111222333,
            first_name="Alice"
        )
        self.assertEqual(str(user_first_only), "Alice (111222333)")
        
        # Test with only telegram_id
        user_minimal = TelegramUserModel.objects.create(
            telegram_id=444555666
        )
        self.assertEqual(str(user_minimal), "User 444555666")
    
    def test_full_name_property(self):
        """Test full_name property."""
        # Test with both names
        self.assertEqual(self.test_user.full_name, "John Doe")
        
        # Test with only first name
        user_first_only = TelegramUserModel.objects.create(
            telegram_id=111222333,
            first_name="Alice"
        )
        self.assertEqual(user_first_only.full_name, "Alice")
        
        # Test with only last name
        user_last_only = TelegramUserModel.objects.create(
            telegram_id=444555666,
            last_name="Brown"
        )
        self.assertEqual(user_last_only.full_name, "Brown")
        
        # Test with no names
        user_no_names = TelegramUserModel.objects.create(
            telegram_id=777888999
        )
        self.assertEqual(user_no_names.full_name, "Unknown")
    
    def test_update_last_seen(self):
        """Test update_last_seen method."""
        original_last_seen = self.test_user.last_seen
        self.test_user.update_last_seen()
        self.test_user.refresh_from_db()
        
        self.assertGreater(self.test_user.last_seen, original_last_seen)
        self.assertAlmostEqual(
            self.test_user.last_seen.timestamp(),
            timezone.now().timestamp(),
            delta=5  # Allow 5 seconds difference
        )
    
    def test_unique_telegram_id(self):
        """Test that telegram_id must be unique."""
        with self.assertRaises(IntegrityError):
            TelegramUserModel.objects.create(
                telegram_id=123456789,  # Same as existing
                first_name="Duplicate"
            )
    
    def test_model_meta(self):
        """Test model meta configuration."""
        self.assertEqual(TelegramUserModel._meta.db_table, 'telegram_users')
        self.assertEqual(TelegramUserModel._meta.verbose_name, 'Telegram User')
        self.assertEqual(TelegramUserModel._meta.verbose_name_plural, 'Telegram Users')
        self.assertEqual(TelegramUserModel._meta.ordering, ['-created_at'])


class TelegramUserServiceTest(TestCase):
    """Test cases for TelegramUserService."""
    
    def setUp(self):
        """Set up test data."""
        self.mock_telegram_user = Mock(spec=TelegramUser)
        self.mock_telegram_user.id = 123456789
        self.mock_telegram_user.first_name = "John"
        self.mock_telegram_user.last_name = "Doe"
        self.mock_telegram_user.username = "johndoe"
    
    def test_get_or_create_user_new_user(self):
        """Test creating a new user."""
        user, created = TelegramUserService.get_or_create_user(self.mock_telegram_user)
        
        self.assertTrue(created)
        self.assertEqual(user.telegram_id, 123456789)
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.username, "johndoe")
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.last_seen)
    
    def test_get_or_create_user_existing_user(self):
        """Test getting an existing user."""
        # Create user first
        TelegramUserService.get_or_create_user(self.mock_telegram_user)
        
        # Try to get/create again
        user, created = TelegramUserService.get_or_create_user(self.mock_telegram_user)
        
        self.assertFalse(created)
        self.assertEqual(user.telegram_id, 123456789)
    
    def test_get_or_create_user_update_existing(self):
        """Test updating an existing user's information."""
        # Create user first
        TelegramUserService.get_or_create_user(self.mock_telegram_user)
        
        # Update the mock user
        self.mock_telegram_user.first_name = "Johnny"
        self.mock_telegram_user.last_name = "Smith"
        self.mock_telegram_user.username = "johnnysmith"
        
        user, created = TelegramUserService.get_or_create_user(self.mock_telegram_user)
        
        self.assertFalse(created)
        self.assertEqual(user.first_name, "Johnny")
        self.assertEqual(user.last_name, "Smith")
        self.assertEqual(user.username, "johnnysmith")
    
    def test_get_user_by_telegram_id_existing(self):
        """Test getting user by telegram_id when user exists."""
        TelegramUserService.get_or_create_user(self.mock_telegram_user)
        
        user = TelegramUserService.get_user_by_telegram_id(123456789)
        
        self.assertIsNotNone(user)
        self.assertEqual(user.telegram_id, 123456789)
    
    def test_get_user_by_telegram_id_not_found(self):
        """Test getting user by telegram_id when user doesn't exist."""
        user = TelegramUserService.get_user_by_telegram_id(999999999)
        
        self.assertIsNone(user)
    
    def test_update_user_last_seen_existing(self):
        """Test updating last_seen for existing user."""
        TelegramUserService.get_or_create_user(self.mock_telegram_user)
        
        result = TelegramUserService.update_user_last_seen(123456789)
        
        self.assertTrue(result)
        
        user = TelegramUserService.get_user_by_telegram_id(123456789)
        self.assertIsNotNone(user.last_seen)
    
    def test_update_user_last_seen_not_found(self):
        """Test updating last_seen for non-existing user."""
        result = TelegramUserService.update_user_last_seen(999999999)
        
        self.assertFalse(result)
    
    def test_get_user_stats(self):
        """Test getting user statistics."""
        # Create some test users
        for i in range(3):
            mock_user = Mock(spec=TelegramUser)
            mock_user.id = 100000000 + i
            mock_user.first_name = f"User{i}"
            mock_user.last_name = None
            mock_user.username = f"user{i}"
            TelegramUserService.get_or_create_user(mock_user)
        
        stats = TelegramUserService.get_user_stats()
        
        self.assertEqual(stats['total_users'], 3)
        self.assertEqual(stats['active_users_30d'], 3)  # All recent
    
    def test_get_user_stats_with_old_users(self):
        """Test user stats with old users."""
        # Create a recent user
        recent_user = Mock(spec=TelegramUser)
        recent_user.id = 111111111
        recent_user.first_name = "Recent"
        recent_user.last_name = None
        recent_user.username = "recent"
        TelegramUserService.get_or_create_user(recent_user)
        
        # Create an old user manually
        old_user = TelegramUserModel.objects.create(
            telegram_id=222222222,
            first_name="Old",
            last_seen=timezone.now() - timedelta(days=35)
        )
        
        stats = TelegramUserService.get_user_stats()
        
        self.assertEqual(stats['total_users'], 2)
        self.assertEqual(stats['active_users_30d'], 1)  # Only recent user
    
    def test_get_users_list(self):
        """Test getting paginated users list."""
        # Create multiple users
        for i in range(5):
            mock_user = Mock(spec=TelegramUser)
            mock_user.id = 200000000 + i
            mock_user.first_name = f"User{i}"
            mock_user.last_name = None
            mock_user.username = f"user{i}"
            TelegramUserService.get_or_create_user(mock_user)
        
        users_list, total_count = TelegramUserService.get_users_list(page=1, page_size=3)
        
        self.assertEqual(len(users_list), 3)
        self.assertEqual(total_count, 5)
    
    def test_get_users_list_pagination(self):
        """Test pagination of users list."""
        # Create multiple users
        for i in range(5):
            mock_user = Mock(spec=TelegramUser)
            mock_user.id = 300000000 + i
            mock_user.first_name = f"User{i}"
            mock_user.last_name = None
            mock_user.username = f"user{i}"
            TelegramUserService.get_or_create_user(mock_user)
        
        # Test second page
        users_list, total_count = TelegramUserService.get_users_list(page=2, page_size=3)
        
        self.assertEqual(len(users_list), 2)  # Remaining users
        self.assertEqual(total_count, 5)
    
    def test_get_users_list_empty(self):
        """Test getting users list when no users exist."""
        users_list, total_count = TelegramUserService.get_users_list()
        
        self.assertEqual(len(users_list), 0)
        self.assertEqual(total_count, 0)


class TelegramBotHandlersTest(TestCase):
    """Test cases for Telegram bot handlers."""
    
    def setUp(self):
        """Set up test data."""
        self.mock_update = Mock(spec=Update)
        self.mock_context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        
        # Mock user
        self.mock_telegram_user = Mock(spec=TelegramUser)
        self.mock_telegram_user.id = 123456789
        self.mock_telegram_user.first_name = "John"
        self.mock_telegram_user.last_name = "Doe"
        self.mock_telegram_user.username = "johndoe"
        
        # Mock message
        self.mock_message = Mock(spec=Message)
        self.mock_message.reply_text = AsyncMock()
        self.mock_message.text = "Test message"
        
        # Mock chat
        self.mock_chat = Mock(spec=Chat)
        self.mock_chat.id = 123456789
        
        # Configure mocks
        self.mock_update.effective_user = self.mock_telegram_user
        self.mock_update.message = self.mock_message
        self.mock_message.chat = self.mock_chat
    
    @pytest.mark.asyncio
    async def test_register_user_success(self):
        """Test successful user registration."""
        with patch('telegram_bot.bot.TelegramUserService.get_or_create_user') as mock_service:
            mock_service.return_value = (Mock(), True)
            
            await register_user(self.mock_update, self.mock_context)
            
            mock_service.assert_called_once_with(self.mock_telegram_user)
    
    @pytest.mark.asyncio
    async def test_register_user_no_user(self):
        """Test user registration when no user in update."""
        self.mock_update.effective_user = None
        
        with patch('telegram_bot.bot.TelegramUserService.get_or_create_user') as mock_service:
            await register_user(self.mock_update, self.mock_context)
            
            mock_service.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_register_user_exception(self):
        """Test user registration with exception."""
        with patch('telegram_bot.bot.TelegramUserService.get_or_create_user') as mock_service:
            mock_service.side_effect = Exception("Database error")
            
            # Should not raise exception
            await register_user(self.mock_update, self.mock_context)
            
            mock_service.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_command(self):
        """Test /start command handler."""
        with patch('telegram_bot.bot.register_user') as mock_register, \
             patch('telegram_bot.bot.get_template') as mock_template:
            
            mock_template_instance = Mock()
            mock_template_instance.render.return_value = "Welcome message"
            mock_template.return_value = mock_template_instance
            
            await start(self.mock_update, self.mock_context)
            
            mock_register.assert_called_once_with(self.mock_update, self.mock_context)
            mock_template.assert_called_once_with('telegram_bot/start.txt')
            mock_template_instance.render.assert_called_once()
            self.mock_message.reply_text.assert_called_once_with("Welcome message")
    
    @pytest.mark.asyncio
    async def test_schedule_command_with_games(self):
        """Test /schedule command with games."""
        from nhl_data.models import Game
        
        # Create mock games
        mock_games = [
            Mock(spec=Game),
            Mock(spec=Game)
        ]
        
        with patch('telegram_bot.bot.register_user') as mock_register, \
             patch('telegram_bot.bot.sync_to_async') as mock_sync_async, \
             patch('telegram_bot.bot.get_template') as mock_template:
            
            # Mock sync_to_async to return a function that returns a coroutine
            def mock_sync_func(func):
                async def async_wrapper(*args, **kwargs):
                    return mock_games
                return async_wrapper
            
            mock_sync_async.side_effect = mock_sync_func
            mock_template_instance = Mock()
            mock_template_instance.render.return_value = "Schedule message"
            mock_template.return_value = mock_template_instance
            
            await schedule(self.mock_update, self.mock_context)
            
            mock_register.assert_called_once()
            self.mock_message.reply_text.assert_called_once_with("Schedule message", parse_mode="Markdown")
    
    @pytest.mark.asyncio
    async def test_schedule_command_no_games(self):
        """Test /schedule command with no games."""
        with patch('telegram_bot.bot.register_user') as mock_register, \
             patch('telegram_bot.bot.sync_to_async') as mock_sync_async, \
             patch('telegram_bot.bot.get_template') as mock_template:
            
            # Mock sync_to_async to return a function that returns a coroutine
            def mock_sync_func(func):
                async def async_wrapper(*args, **kwargs):
                    return []
                return async_wrapper
            
            mock_sync_async.side_effect = mock_sync_func
            mock_template_instance = Mock()
            mock_template_instance.render.return_value = "No games message"
            mock_template.return_value = mock_template_instance
            
            await schedule(self.mock_update, self.mock_context)
            
            mock_register.assert_called_once()
            self.mock_message.reply_text.assert_called_once_with("No games message", parse_mode="Markdown")
    
    @pytest.mark.asyncio
    async def test_schedule_command_exception(self):
        """Test /schedule command with exception."""
        with patch('telegram_bot.bot.register_user') as mock_register, \
             patch('telegram_bot.bot.sync_to_async') as mock_sync_async, \
             patch('telegram_bot.bot.get_template') as mock_template:
            
            mock_sync_async.side_effect = Exception("Database error")
            mock_template_instance = Mock()
            mock_template_instance.render.return_value = "Error message"
            mock_template.return_value = mock_template_instance
            
            await schedule(self.mock_update, self.mock_context)
            
            mock_register.assert_called_once()
            self.mock_message.reply_text.assert_called_once_with("Error message")
    
    @pytest.mark.asyncio
    async def test_users_command_page_1(self):
        """Test /users command with page 1."""
        self.mock_context.args = []
        
        with patch('telegram_bot.bot.register_user') as mock_register, \
             patch('telegram_bot.bot.sync_to_async') as mock_sync_async, \
             patch('telegram_bot.bot.get_template') as mock_template:
            
            mock_users = [Mock(), Mock()]
            mock_stats = {
                'total_users': 2, 
                'active_users_30d': 1,
                'premium_users': 0,
                'verified_users': 0
            }
            
            def mock_sync_func(func):
                async def async_wrapper(*args, **kwargs):
                    if 'get_users_list' in str(func):
                        return (mock_users, 2)
                    elif 'get_user_stats' in str(func):
                        return mock_stats
                    return Mock()
                return async_wrapper
            
            mock_sync_async.side_effect = mock_sync_func
            mock_template_instance = Mock()
            mock_template_instance.render.return_value = "Users message"
            mock_template.return_value = mock_template_instance
            
            await users(self.mock_update, self.mock_context)
            
            mock_register.assert_called_once()
            self.mock_message.reply_text.assert_called_once_with("Users message", parse_mode="Markdown")
    
    @pytest.mark.asyncio
    async def test_users_command_with_page(self):
        """Test /users command with specific page."""
        self.mock_context.args = ['2']
        
        with patch('telegram_bot.bot.register_user') as mock_register, \
             patch('telegram_bot.bot.sync_to_async') as mock_sync_async, \
             patch('telegram_bot.bot.get_template') as mock_template:
            
            mock_users = [Mock()]
            mock_stats = {
                'total_users': 5, 
                'active_users_30d': 3,
                'premium_users': 0,
                'verified_users': 0
            }
            
            def mock_sync_func(func):
                async def async_wrapper(*args, **kwargs):
                    if 'get_users_list' in str(func):
                        return (mock_users, 5)
                    elif 'get_user_stats' in str(func):
                        return mock_stats
                    return Mock()
                return async_wrapper
            
            mock_sync_async.side_effect = mock_sync_func
            mock_template_instance = Mock()
            mock_template_instance.render.return_value = "Users page 2"
            mock_template.return_value = mock_template_instance
            
            await users(self.mock_update, self.mock_context)
            
            mock_register.assert_called_once()
            self.mock_message.reply_text.assert_called_once_with("Users page 2", parse_mode="Markdown")
    
    @pytest.mark.asyncio
    async def test_users_command_exception(self):
        """Test /users command with exception."""
        with patch('telegram_bot.bot.register_user') as mock_register, \
             patch('telegram_bot.bot.sync_to_async') as mock_sync_async:
            
            mock_sync_async.side_effect = Exception("Database error")
            
            await users(self.mock_update, self.mock_context)
            
            mock_register.assert_called_once()
            self.mock_message.reply_text.assert_called_once_with("❌ Error retrieving users list. Please try again later.")
    
    @pytest.mark.asyncio
    async def test_handle_message(self):
        """Test handle_message function."""
        with patch('telegram_bot.bot.register_user') as mock_register:
            await handle_message(self.mock_update, self.mock_context)
            
            mock_register.assert_called_once_with(self.mock_update, self.mock_context)


class TelegramBotTemplatesTest(TestCase):
    """Test cases for Telegram bot templates."""
    
    def test_start_template(self):
        """Test start template rendering."""
        template = get_template('telegram_bot/start.txt')
        rendered = template.render()
        
        self.assertIn("Hello! I am your bot.", rendered)
    
    def test_schedule_template(self):
        """Test schedule template rendering."""
        template = get_template('telegram_bot/schedule.txt')
        
        # Mock game objects
        mock_game1 = Mock()
        mock_game1.away_team_abbreviation = "TOR"
        mock_game1.home_team_abbreviation = "MTL"
        mock_game1.start_time_utc = datetime(2024, 1, 15, 19, 0)
        
        mock_game2 = Mock()
        mock_game2.away_team_abbreviation = "BOS"
        mock_game2.home_team_abbreviation = "NYR"
        mock_game2.start_time_utc = datetime(2024, 1, 15, 20, 30)
        
        context = {
            'current_date': '15.01.2024',
            'games': [mock_game1, mock_game2]
        }
        
        rendered = template.render(context)
        
        self.assertIn("Upcoming NHL Games", rendered)
        self.assertIn("15.01.2024", rendered)
        self.assertIn("TOR @ MTL", rendered)
        self.assertIn("BOS @ NYR", rendered)
    
    def test_schedule_empty_template(self):
        """Test schedule empty template rendering."""
        template = get_template('telegram_bot/schedule_empty.txt')
        rendered = template.render()
        
        # Template should exist and render without errors
        self.assertIsInstance(rendered, str)
    
    def test_schedule_error_template(self):
        """Test schedule error template rendering."""
        template = get_template('telegram_bot/schedule_error.txt')
        rendered = template.render()
        
        # Template should exist and render without errors
        self.assertIsInstance(rendered, str)
    
    def test_users_template(self):
        """Test users template rendering."""
        template = get_template('telegram_bot/users.txt')
        
        # Mock user objects
        mock_user1 = Mock()
        mock_user1.full_name = "John Doe"
        mock_user1.telegram_id = 123456789
        mock_user1.username = "johndoe"
        mock_user1.last_seen = datetime(2024, 1, 15, 10, 0)
        mock_user1.created_at = datetime(2024, 1, 1, 10, 0)
        
        mock_user2 = Mock()
        mock_user2.full_name = "Jane Smith"
        mock_user2.telegram_id = 987654321
        mock_user2.username = None
        mock_user2.last_seen = datetime(2024, 1, 14, 15, 30)
        mock_user2.created_at = datetime(2024, 1, 2, 15, 30)
        
        context = {
            'users': [mock_user1, mock_user2],
            'total_users': 2,
            'active_users': 1,
            'premium_users': 0,
            'verified_users': 0,
            'current_page': 1,
            'total_pages': 1,
            'next_page': None
        }
        
        rendered = template.render(context)
        
        self.assertIn("Saved Users List", rendered)
        self.assertIn("Total Users: 2", rendered)
        self.assertIn("Active (30d): 1", rendered)
        self.assertIn("John Doe", rendered)
        self.assertIn("Jane Smith", rendered)
        self.assertIn("@johndoe", rendered)
        self.assertIn("N/A", rendered)  # For user without username
    
    def test_users_empty_template(self):
        """Test users empty template rendering."""
        template = get_template('telegram_bot/users_empty.txt')
        rendered = template.render()
        
        # Template should exist and render without errors
        self.assertIsInstance(rendered, str)


class TelegramUserAdminTest(TestCase):
    """Test cases for TelegramUser admin interface."""
    
    def setUp(self):
        """Set up test data."""
        self.site = AdminSite()
        self.admin = TelegramUserAdmin(TelegramUserModel, self.site)
        
        # Create test user
        self.test_user = TelegramUserModel.objects.create(
            telegram_id=123456789,
            first_name="John",
            last_name="Doe",
            username="johndoe"
        )
    
    def test_list_display(self):
        """Test admin list display configuration."""
        expected_fields = [
            'telegram_id', 'username', 'full_name', 
            'created_at', 'last_seen'
        ]
        self.assertEqual(self.admin.list_display, expected_fields)
    
    def test_list_filter(self):
        """Test admin list filter configuration."""
        expected_filters = ['created_at', 'last_seen']
        self.assertEqual(self.admin.list_filter, expected_filters)
    
    def test_search_fields(self):
        """Test admin search fields configuration."""
        expected_fields = ['telegram_id', 'username', 'first_name', 'last_name']
        self.assertEqual(self.admin.search_fields, expected_fields)
    
    def test_readonly_fields(self):
        """Test admin readonly fields configuration."""
        expected_fields = ['telegram_id', 'created_at', 'updated_at']
        self.assertEqual(self.admin.readonly_fields, expected_fields)
    
    def test_ordering(self):
        """Test admin ordering configuration."""
        expected_ordering = ['-created_at']
        self.assertEqual(self.admin.ordering, expected_ordering)
    
    def test_fieldsets(self):
        """Test admin fieldsets configuration."""
        fieldsets = self.admin.fieldsets
        
        # Check that we have the expected fieldsets
        self.assertEqual(len(fieldsets), 2)
        
        # Check basic information fieldset
        basic_info = fieldsets[0]
        self.assertEqual(basic_info[0], 'Basic Information')
        self.assertIn('telegram_id', basic_info[1]['fields'])
        self.assertIn('first_name', basic_info[1]['fields'])
        self.assertIn('last_name', basic_info[1]['fields'])
        self.assertIn('username', basic_info[1]['fields'])
        
        # Check timestamps fieldset
        timestamps = fieldsets[1]
        self.assertEqual(timestamps[0], 'Timestamps')
        self.assertIn('created_at', timestamps[1]['fields'])
        self.assertIn('updated_at', timestamps[1]['fields'])
        self.assertIn('last_seen', timestamps[1]['fields'])
        self.assertIn('collapse', timestamps[1]['classes'])
    
    def test_get_queryset_optimization(self):
        """Test admin queryset optimization."""
        # Create a mock request
        request = Mock()
        
        # Test that get_queryset returns optimized queryset
        queryset = self.admin.get_queryset(request)
        
        # Should not raise any exceptions
        self.assertIsNotNone(queryset)
    
    def test_admin_registration(self):
        """Test that admin is properly registered."""
        from django.contrib import admin
        from .models import TelegramUser
        
        # Check that TelegramUser is registered with admin
        self.assertIn(TelegramUser, admin.site._registry)
        self.assertIsInstance(admin.site._registry[TelegramUser], TelegramUserAdmin)


class TelegramBotIntegrationTest(TransactionTestCase):
    """Integration tests for the complete telegram_bot functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.mock_telegram_user = Mock(spec=TelegramUser)
        self.mock_telegram_user.id = 123456789
        self.mock_telegram_user.first_name = "John"
        self.mock_telegram_user.last_name = "Doe"
        self.mock_telegram_user.username = "johndoe"
    
    def test_complete_user_lifecycle(self):
        """Test complete user lifecycle from creation to retrieval."""
        # Create user
        user, created = TelegramUserService.get_or_create_user(self.mock_telegram_user)
        self.assertTrue(created)
        self.assertEqual(user.telegram_id, 123456789)
        
        # Update user
        self.mock_telegram_user.first_name = "Johnny"
        user, created = TelegramUserService.get_or_create_user(self.mock_telegram_user)
        self.assertFalse(created)
        self.assertEqual(user.first_name, "Johnny")
        
        # Retrieve user
        retrieved_user = TelegramUserService.get_user_by_telegram_id(123456789)
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.first_name, "Johnny")
        
        # Update last seen
        result = TelegramUserService.update_user_last_seen(123456789)
        self.assertTrue(result)
        
        # Get stats
        stats = TelegramUserService.get_user_stats()
        self.assertEqual(stats['total_users'], 1)
        self.assertEqual(stats['active_users_30d'], 1)
        
        # Get users list
        users_list, total_count = TelegramUserService.get_users_list()
        self.assertEqual(len(users_list), 1)
        self.assertEqual(total_count, 1)
    
    def test_multiple_users_management(self):
        """Test managing multiple users."""
        # Create multiple users
        users_data = [
            (111111111, "Alice", "Johnson", "alice"),
            (222222222, "Bob", "Wilson", "bob"),
            (333333333, "Charlie", "Brown", "charlie"),
        ]
        
        created_users = []
        for telegram_id, first_name, last_name, username in users_data:
            mock_user = Mock(spec=TelegramUser)
            mock_user.id = telegram_id
            mock_user.first_name = first_name
            mock_user.last_name = last_name
            mock_user.username = username
            
            user, created = TelegramUserService.get_or_create_user(mock_user)
            self.assertTrue(created)
            created_users.append(user)
        
        # Test stats
        stats = TelegramUserService.get_user_stats()
        self.assertEqual(stats['total_users'], 3)
        self.assertEqual(stats['active_users_30d'], 3)
        
        # Test pagination
        users_list, total_count = TelegramUserService.get_users_list(page=1, page_size=2)
        self.assertEqual(len(users_list), 2)
        self.assertEqual(total_count, 3)
        
        # Test second page
        users_list, total_count = TelegramUserService.get_users_list(page=2, page_size=2)
        self.assertEqual(len(users_list), 1)
        self.assertEqual(total_count, 3)
    
    def test_error_handling(self):
        """Test error handling in service methods."""
        # Test getting non-existent user
        user = TelegramUserService.get_user_by_telegram_id(999999999)
        self.assertIsNone(user)
        
        # Test updating non-existent user
        result = TelegramUserService.update_user_last_seen(999999999)
        self.assertFalse(result)
        
        # Test stats with no users
        stats = TelegramUserService.get_user_stats()
        self.assertEqual(stats['total_users'], 0)
        self.assertEqual(stats['active_users_30d'], 0)
        
        # Test users list with no users
        users_list, total_count = TelegramUserService.get_users_list()
        self.assertEqual(len(users_list), 0)
        self.assertEqual(total_count, 0)
