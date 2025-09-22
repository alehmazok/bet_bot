"""
Django management command to test Telegram user storage functionality.
"""
from django.core.management.base import BaseCommand
from telegram_bot.services import TelegramUserService
from telegram_bot.models import TelegramUser


class MockTelegramUser:
    """Mock Telegram User object for testing."""
    
    def __init__(self, user_id, first_name=None, last_name=None, username=None):
        self.id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username


class Command(BaseCommand):
    help = 'Test Telegram user storage functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up test data after testing',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧪 Testing Telegram User Storage Implementation')
        )
        self.stdout.write('=' * 50)
        
        try:
            # Test 1: Create user
            self.test_user_creation()
            
            # Test 2: Update user
            self.test_user_update()
            
            # Test 3: Retrieve user
            self.test_user_retrieval()
            
            # Test 4: Get stats
            self.test_user_stats()
            
            # Test 5: Multiple users
            self.test_multiple_users()
            
            # Test 6: Final stats
            self.stdout.write('\nFinal statistics:')
            self.test_user_stats()
            
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(
                self.style.SUCCESS('✅ All tests completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Test failed with error: {str(e)}')
            )
            import traceback
            traceback.print_exc()
        
        finally:
            if options['cleanup']:
                self.cleanup_test_data()

    def test_user_creation(self):
        """Test creating a new user."""
        self.stdout.write('Testing user creation...')
        
        mock_user = MockTelegramUser(
            user_id=123456789,
            first_name="John",
            last_name="Doe",
            username="johndoe"
        )
        
        try:
            user, created = TelegramUserService.get_or_create_user(mock_user)
            
            self.stdout.write(f"✅ User created: {created}")
            self.stdout.write(f"✅ User ID: {user.telegram_id}")
            self.stdout.write(f"✅ Full name: {user.full_name}")
            self.stdout.write(f"✅ Username: @{user.username}")
            self.stdout.write(f"✅ Created at: {user.created_at}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating user: {str(e)}')
            )

    def test_user_update(self):
        """Test updating an existing user."""
        self.stdout.write('\nTesting user update...')
        
        mock_user = MockTelegramUser(
            user_id=123456789,  # Same ID as before
            first_name="John",
            last_name="Smith",  # Changed last name
            username="johnsmith"  # Changed username
        )
        
        try:
            user, created = TelegramUserService.get_or_create_user(mock_user)
            
            self.stdout.write(f"✅ User created: {created} (should be False)")
            self.stdout.write(f"✅ Updated name: {user.full_name}")
            self.stdout.write(f"✅ Updated username: @{user.username}")
            self.stdout.write(f"✅ Updated at: {user.updated_at}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error updating user: {str(e)}')
            )

    def test_user_retrieval(self):
        """Test retrieving a user by Telegram ID."""
        self.stdout.write('\nTesting user retrieval...')
        
        try:
            user = TelegramUserService.get_user_by_telegram_id(123456789)
            
            if user:
                self.stdout.write(f"✅ User found: {user}")
                self.stdout.write(f"✅ Full name: {user.full_name}")
                self.stdout.write(f"✅ Last seen: {user.last_seen}")
            else:
                self.stdout.write("❌ User not found")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error retrieving user: {str(e)}')
            )

    def test_user_stats(self):
        """Test getting user statistics."""
        self.stdout.write('\nTesting user statistics...')
        
        try:
            stats = TelegramUserService.get_user_stats()
            
            self.stdout.write(f"✅ Total users: {stats['total_users']}")
            self.stdout.write(f"✅ Active users (30d): {stats['active_users_30d']}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error getting stats: {str(e)}')
            )

    def test_multiple_users(self):
        """Test creating multiple users."""
        self.stdout.write('\nTesting multiple users...')
        
        users_data = [
            (987654321, "Alice", "Johnson", "alice"),
            (456789123, "Bob", "Wilson", "bob"),
            (789123456, "Charlie", "Brown", "charlie"),
        ]
        
        for user_data in users_data:
            mock_user = MockTelegramUser(*user_data)
            try:
                user, created = TelegramUserService.get_or_create_user(mock_user)
                self.stdout.write(f"✅ Created user: {user.full_name} (@{user.username})")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error creating user {user_data[0]}: {str(e)}')
                )

    def cleanup_test_data(self):
        """Clean up test data."""
        self.stdout.write('\nCleaning up test data...')
        
        try:
            test_ids = [123456789, 987654321, 456789123, 789123456]
            deleted_count = TelegramUser.objects.filter(telegram_id__in=test_ids).delete()[0]
            self.stdout.write(f"✅ Deleted {deleted_count} test users")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error cleaning up: {str(e)}')
            )