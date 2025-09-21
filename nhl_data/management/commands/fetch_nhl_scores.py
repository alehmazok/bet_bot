import requests
from datetime import date, datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from nhl_data.models import Game


class Command(BaseCommand):
    help = 'Fetches NHL game results from the NHL API and stores them in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to fetch (YYYY-MM-DD format). Defaults to today.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if games already exist for the date',
        )

    def handle(self, *args, **options):
        # Determine the date to fetch
        if options['date']:
            try:
                fetch_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Date must be in YYYY-MM-DD format')
        else:
            fetch_date = date.today()

        self.stdout.write(f"Fetching NHL scores for {fetch_date}")

        # Build the API URL
        api_url = f"https://api-web.nhle.com/v1/score/{fetch_date.strftime('%Y-%m-%d')}"
        
        try:
            # Fetch data from NHL API
            self.stdout.write(f"Fetching data from: {api_url}")
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            games_data = data.get('games', [])
            
            if not games_data:
                self.stdout.write(
                    self.style.WARNING(f"No games found for {fetch_date}")
                )
                return

            processed_count = 0
            
            # Process each game
            with transaction.atomic():
                for game_data in games_data:
                    try:
                        processed = self._process_game(game_data, options['force'])
                        if processed:
                            processed_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error processing game {game_data.get('id', 'unknown')}: {str(e)}")
                        )
                        continue

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully processed {processed_count} games for {fetch_date}'
                )
            )

        except requests.RequestException as e:
            error_msg = f"Failed to fetch data from NHL API: {str(e)}"
            raise CommandError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            raise CommandError(error_msg)

    def _process_game(self, game_data, force_update=False):
        """Process a single game from the API data"""
        game_id = game_data['id']
        
        # Check if game already exists
        existing_game = Game.objects.filter(game_id=game_id).first()
        if existing_game and not force_update:
            self.stdout.write(f"Game {game_id} already exists, skipping...")
            return False

        # Extract basic game info
        season = game_data['season']
        game_type = game_data['gameType']
        game_date = datetime.strptime(game_data['gameDate'], '%Y-%m-%d').date()
        start_time_utc = datetime.fromisoformat(
            game_data['startTimeUTC'].replace('Z', '+00:00')
        )

        # Extract home team data
        home_team_data = game_data['homeTeam']
        home_team_id = home_team_data['id']
        home_team_name = home_team_data['name']['default']
        home_team_abbrev = home_team_data['abbrev']
        home_team_score = home_team_data.get('score')
        home_team_sog = home_team_data.get('sog')
        home_team_record = home_team_data.get('record', '')
        home_team_logo = home_team_data.get('logo', '')

        # Extract away team data
        away_team_data = game_data['awayTeam']
        away_team_id = away_team_data['id']
        away_team_name = away_team_data['name']['default']
        away_team_abbrev = away_team_data['abbrev']
        away_team_score = away_team_data.get('score')
        away_team_sog = away_team_data.get('sog')
        away_team_record = away_team_data.get('record', '')
        away_team_logo = away_team_data.get('logo', '')

        # Extract venue info
        venue_name = ''
        if 'venue' in game_data and game_data['venue']:
            venue_name = game_data['venue']['default']

        # Create or update game
        game_defaults = {
            'season': season,
            'game_type': game_type,
            'game_date': game_date,
            'home_team_id': home_team_id,
            'home_team_name': home_team_name,
            'home_team_abbreviation': home_team_abbrev,
            'home_team_score': home_team_score,
            'home_team_sog': home_team_sog,
            'home_team_record': home_team_record,
            'home_team_logo_url': home_team_logo,
            'away_team_id': away_team_id,
            'away_team_name': away_team_name,
            'away_team_abbreviation': away_team_abbrev,
            'away_team_score': away_team_score,
            'away_team_sog': away_team_sog,
            'away_team_record': away_team_record,
            'away_team_logo_url': away_team_logo,
            'venue_name': venue_name,
            'start_time_utc': start_time_utc,
            'eastern_utc_offset': game_data.get('easternUTCOffset', ''),
            'venue_utc_offset': game_data.get('venueUTCOffset', ''),
            'venue_timezone': game_data.get('venueTimezone', ''),
            'game_state': game_data.get('gameState', 'FUT'),
            'game_schedule_state': game_data.get('gameScheduleState', 'OK'),
            'neutral_site': game_data.get('neutralSite', False),
            'game_center_link': game_data.get('gameCenterLink', ''),
            'tickets_link': game_data.get('ticketsLink', ''),
        }

        game, created = Game.objects.update_or_create(
            game_id=game_id,
            defaults=game_defaults
        )

        action = "Created" if created else "Updated"
        self.stdout.write(f"{action} game: {game}")
        return True