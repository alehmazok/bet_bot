# NHL Game Data Fetcher

A simple Django command that fetches NHL game results daily from the official NHL API.

## Features

- Fetches game data from `https://api-web.nhle.com/v1/score/YYYY-MM-DD`
- Stores complete game information in a single Django model
- Automatic daily scheduling via cron job
- Django admin interface for data management

## Model

The `Game` model stores all NHL game information including:
- Game ID, season, type, and date
- Home and away team details (name, abbreviation, scores, records, logos)
- Venue and timing information
- Game state and links

## Usage

### Manual Execution

```bash
# Fetch today's games
python manage.py fetch_nhl_scores

# Fetch specific date
python manage.py fetch_nhl_scores --date=2025-09-21

# Force update existing games
python manage.py fetch_nhl_scores --force
```

### Daily Scheduling

Run the setup script to create a daily cron job:

```bash
./setup_daily_fetch.sh
```

This creates a cron job that runs daily at 9:00 AM:
```
0 9 * * * cd /workspace && python3 manage.py fetch_nhl_scores >> /workspace/nhl_fetch.log 2>&1
```

### Admin Interface

Access the Django admin at `/admin/` to view and manage game data with filtering by:
- Game date
- Game state (Future, Live, Final, etc.)
- Teams
- Season

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements/base.txt
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Test the command:
   ```bash
   python manage.py fetch_nhl_scores --date=2025-09-21
   ```

## Logs

View fetch logs:
```bash
tail -f /workspace/nhl_fetch.log
```