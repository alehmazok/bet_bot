# NHL Data Fetcher

A Django application that automatically fetches NHL game results from the official NHL API and stores them in your database.

## Features

- **Automatic Daily Fetching**: Configurable scheduling to fetch NHL game data daily
- **Comprehensive Data Model**: Stores teams, games, venues, TV broadcasts, and fetch logs
- **Robust Error Handling**: Includes retry logic and comprehensive logging
- **Flexible Scheduling**: Supports both cron jobs and systemd timers
- **Admin Interface**: Full Django admin integration for data management
- **API Integration**: Uses the official NHL API (api-web.nhle.com)

## Models

### Team
- Stores NHL team information (name, abbreviation, logo)
- Automatically created from API data

### Game
- Complete game information including:
  - Teams, scores, and game state
  - Venue and timing details
  - Team records and statistics
  - Links to NHL GameCenter and tickets

### Venue
- Arena/venue information with timezone data

### TVBroadcast
- Television broadcast details for each game

### GameFetchLog
- Audit trail of all API fetch attempts

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements/base.txt
   ```

2. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

3. **Test the Command**:
   ```bash
   python manage.py fetch_nhl_scores --date=2025-09-21
   ```

## Usage

### Manual Execution

Fetch today's games:
```bash
python manage.py fetch_nhl_scores
```

Fetch specific date:
```bash
python manage.py fetch_nhl_scores --date=2025-09-21
```

Force update existing games:
```bash
python manage.py fetch_nhl_scores --force
```

### Automated Scheduling

#### Option 1: Cron Job (Recommended)

Run the setup script:
```bash
python3 setup_nhl_scheduler.py cron
```

Or manually add to crontab:
```bash
# Runs daily at 9:00 AM
0 9 * * * cd /workspace && python3 manage.py fetch_nhl_scores >> /workspace/logs/nhl_fetch.log 2>&1
```

#### Option 2: Systemd Timer

Run the setup script:
```bash
python3 setup_nhl_scheduler.py systemd
```

Check timer status:
```bash
sudo systemctl status nhl-fetcher.timer
```

View logs:
```bash
sudo journalctl -u nhl-fetcher.service
```

## API Details

The application fetches data from:
```
https://api-web.nhle.com/v1/score/YYYY-MM-DD
```

### Sample API Response Structure:
```json
{
  "currentDate": "2025-09-21",
  "games": [
    {
      "id": 2025010007,
      "season": 20252026,
      "gameType": 1,
      "gameDate": "2025-09-21",
      "gameState": "FUT",
      "homeTeam": {
        "id": 1,
        "name": {"default": "Devils"},
        "abbrev": "NJD",
        "score": null
      },
      "awayTeam": {
        "id": 3,
        "name": {"default": "Rangers"},
        "abbrev": "NYR",
        "score": null
      },
      "venue": {"default": "Prudential Center"},
      "startTimeUTC": "2025-09-21T17:00:00Z"
    }
  ]
}
```

## Django Admin

Access the admin interface at `/admin/` to:
- View and manage teams, games, and venues
- Monitor fetch logs and API call history
- Filter games by date, state, and teams
- Export data for analysis

## Monitoring

### Fetch Logs
All API calls are logged in the `GameFetchLog` model with:
- Success/failure status
- Number of games processed
- Error messages (if any)
- API URL called

### Log Files
When using cron jobs, logs are written to:
```
/workspace/logs/nhl_fetch.log
```

View recent logs:
```bash
tail -f /workspace/logs/nhl_fetch.log
```

## Troubleshooting

### Common Issues

1. **Environment Variables Missing**:
   - Ensure `.env` file exists with `SECRET_KEY`
   - Check Django settings configuration

2. **Database Connection Issues**:
   - Verify database settings in settings files
   - Run migrations: `python manage.py migrate`

3. **API Connection Problems**:
   - Check internet connectivity
   - Verify NHL API is accessible
   - Review fetch logs for error details

4. **Cron Job Not Running**:
   - Check cron service: `sudo systemctl status cron`
   - Verify crontab: `crontab -l`
   - Check log files for errors

### Testing

Run the test command to verify everything works:
```bash
python3 setup_nhl_scheduler.py test
```

### Manual Database Check

```python
from nhl_data.models import Game, Team, GameFetchLog

# Check counts
print(f"Teams: {Team.objects.count()}")
print(f"Games: {Game.objects.count()}")
print(f"Fetch logs: {GameFetchLog.objects.count()}")

# Recent games
for game in Game.objects.order_by('-game_date')[:5]:
    print(f"{game} - {game.game_state}")
```

## Configuration

### Time Zone Settings
The application respects Django's `TIME_ZONE` setting. Game times are stored in UTC and can be displayed in local time.

### Scheduling Frequency
Default: Daily at 9:00 AM
- Modify cron expression for different frequency
- NHL games typically occur in the evening, so morning fetching captures previous day's results

### Error Handling
- Network timeouts: 30 seconds
- Failed games are logged but don't stop processing
- Duplicate games are skipped automatically

## Development

### Adding New Fields
1. Update models in `nhl_data/models.py`
2. Create migrations: `python manage.py makemigrations nhl_data`
3. Apply migrations: `python manage.py migrate`
4. Update admin interface in `nhl_data/admin.py`

### API Changes
If the NHL API structure changes:
1. Update the `_process_game()` method in the management command
2. Test with recent data
3. Update model fields if necessary

## Security Notes

- The `.env` file contains sensitive information - keep it secure
- Use production settings for deployed environments
- Consider API rate limiting for high-frequency usage
- Monitor fetch logs for unusual activity

## Support

For issues or questions:
1. Check the Django admin fetch logs
2. Review log files for error details
3. Test manual command execution
4. Verify API accessibility

This implementation provides a robust, maintainable solution for automatically collecting NHL game data with comprehensive error handling and monitoring capabilities.