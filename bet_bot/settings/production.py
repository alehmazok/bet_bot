from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)

# Remember to add your production host here
ALLOWED_HOSTS = ['your_domain.com']

# Database configuration for production
# Reads the DATABASE_URL from the .env file
DATABASES = {
    'default': env.db(),
}