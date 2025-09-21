import requests
from datetime import date, datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from nhl_data.models import Team, Venue, Game, TVBroadcast, GameFetchLog


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
        
        # Initialize fetch log
        fetch_log = GameFetchLog.objects.create(
            fetch_date=fetch_date,
            api_url=api_url,
            success=False
        )

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
                fetch_log.success = True
                fetch_log.save()
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

            # Update fetch log
            fetch_log.success = True
            fetch_log.games_processed = processed_count
            fetch_log.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully processed {processed_count} games for {fetch_date}'
                )
            )

        except requests.RequestException as e:
            error_msg = f"Failed to fetch data from NHL API: {str(e)}"
            fetch_log.error_message = error_msg
            fetch_log.save()
            raise CommandError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            fetch_log.error_message = error_msg
            fetch_log.save()
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

        # Process teams
        home_team = self._get_or_create_team(game_data['homeTeam'])
        away_team = self._get_or_create_team(game_data['awayTeam'])

        # Process venue
        venue = None
        if 'venue' in game_data and game_data['venue']:
            venue_name = game_data['venue']['default']
            venue, _ = Venue.objects.get_or_create(
                name=venue_name,
                defaults={
                    'timezone': game_data.get('venueTimezone', '')
                }
            )

        # Extract score data (if available)
        home_score = game_data['homeTeam'].get('score')
        away_score = game_data['awayTeam'].get('score')
        home_sog = game_data['homeTeam'].get('sog')
        away_sog = game_data['awayTeam'].get('sog')

        # Extract team records
        home_record = game_data['homeTeam'].get('record', '')
        away_record = game_data['awayTeam'].get('record', '')

        # Create or update game
        game_defaults = {
            'season': season,
            'game_type': game_type,
            'game_date': game_date,
            'home_team': home_team,
            'away_team': away_team,
            'venue': venue,
            'start_time_utc': start_time_utc,
            'eastern_utc_offset': game_data.get('easternUTCOffset', ''),
            'venue_utc_offset': game_data.get('venueUTCOffset', ''),
            'venue_timezone': game_data.get('venueTimezone', ''),
            'game_state': game_data.get('gameState', 'FUT'),
            'game_schedule_state': game_data.get('gameScheduleState', 'OK'),
            'neutral_site': game_data.get('neutralSite', False),
            'home_team_score': home_score,
            'away_team_score': away_score,
            'home_team_sog': home_sog,
            'away_team_sog': away_sog,
            'home_team_record': home_record,
            'away_team_record': away_record,
            'game_center_link': game_data.get('gameCenterLink', ''),
            'tickets_link': game_data.get('ticketsLink', ''),
        }

        game, created = Game.objects.update_or_create(
            game_id=game_id,
            defaults=game_defaults
        )

        # Process TV broadcasts
        if 'tvBroadcasts' in game_data:
            # Clear existing broadcasts if updating
            if not created:
                game.tv_broadcasts.all().delete()

            for broadcast_data in game_data['tvBroadcasts']:
                TVBroadcast.objects.create(
                    game=game,
                    broadcast_id=broadcast_data['id'],
                    market=broadcast_data['market'],
                    country_code=broadcast_data['countryCode'],
                    network=broadcast_data['network'],
                    sequence_number=broadcast_data['sequenceNumber']
                )

        action = "Created" if created else "Updated"
        self.stdout.write(f"{action} game: {game}")
        return True

    def _get_or_create_team(self, team_data):
        """Get or create a team from API data"""
        team_id = team_data['id']
        team_name = team_data['name']['default']
        team_abbrev = team_data['abbrev']
        logo_url = team_data.get('logo', '')

        team, created = Team.objects.get_or_create(
            team_id=team_id,
            defaults={
                'name': team_name,
                'abbreviation': team_abbrev,
                'logo_url': logo_url
            }
        )

        # Update team info if it has changed
        if not created:
            updated = False
            if team.name != team_name:
                team.name = team_name
                updated = True
            if team.abbreviation != team_abbrev:
                team.abbreviation = team_abbrev
                updated = True
            if team.logo_url != logo_url:
                team.logo_url = logo_url
                updated = True
            
            if updated:
                team.save()

        return team