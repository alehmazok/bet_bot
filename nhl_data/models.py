from django.db import models
from django.utils import timezone


class Team(models.Model):
    """NHL Team model"""
    team_id = models.IntegerField(unique=True, help_text="NHL API team ID")
    name = models.CharField(max_length=100, help_text="Team name")
    abbreviation = models.CharField(max_length=5, help_text="Team abbreviation")
    logo_url = models.URLField(blank=True, null=True, help_text="Team logo URL")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class Venue(models.Model):
    """NHL Venue/Arena model"""
    name = models.CharField(max_length=200, unique=True)
    timezone = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Game(models.Model):
    """NHL Game model"""
    GAME_STATES = [
        ('FUT', 'Future'),
        ('PRE', 'Pre-Game'),
        ('LIVE', 'Live'),
        ('CRIT', 'Critical'),
        ('FINAL', 'Final'),
        ('OFF', 'Official'),
    ]

    GAME_TYPES = [
        (1, 'Preseason'),
        (2, 'Regular Season'),
        (3, 'Playoffs'),
    ]

    # Basic game info
    game_id = models.BigIntegerField(unique=True, help_text="NHL API game ID")
    season = models.IntegerField(help_text="Season (e.g., 20252026)")
    game_type = models.IntegerField(choices=GAME_TYPES, help_text="Game type")
    game_date = models.DateField(help_text="Game date")
    
    # Teams
    home_team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        related_name='home_games'
    )
    away_team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        related_name='away_games'
    )
    
    # Venue and timing
    venue = models.ForeignKey(
        Venue, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    start_time_utc = models.DateTimeField(help_text="Game start time in UTC")
    eastern_utc_offset = models.CharField(max_length=10, blank=True, null=True)
    venue_utc_offset = models.CharField(max_length=10, blank=True, null=True)
    venue_timezone = models.CharField(max_length=50, blank=True, null=True)
    
    # Game state
    game_state = models.CharField(max_length=10, choices=GAME_STATES)
    game_schedule_state = models.CharField(max_length=20, default='OK')
    neutral_site = models.BooleanField(default=False)
    
    # Scores (null for future games)
    home_team_score = models.IntegerField(null=True, blank=True)
    away_team_score = models.IntegerField(null=True, blank=True)
    home_team_sog = models.IntegerField(null=True, blank=True, help_text="Shots on goal")
    away_team_sog = models.IntegerField(null=True, blank=True, help_text="Shots on goal")
    
    # Team records (for context)
    home_team_record = models.CharField(max_length=20, blank=True, null=True)
    away_team_record = models.CharField(max_length=20, blank=True, null=True)
    
    # Links
    game_center_link = models.CharField(max_length=200, blank=True, null=True)
    tickets_link = models.URLField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-game_date', '-start_time_utc']
        indexes = [
            models.Index(fields=['game_date']),
            models.Index(fields=['game_state']),
            models.Index(fields=['season', 'game_type']),
        ]

    def __str__(self):
        return f"{self.away_team.abbreviation} @ {self.home_team.abbreviation} ({self.game_date})"

    @property
    def is_final(self):
        return self.game_state in ['FINAL', 'OFF']

    @property
    def winner(self):
        """Returns the winning team if game is final"""
        if not self.is_final or self.home_team_score is None or self.away_team_score is None:
            return None
        
        if self.home_team_score > self.away_team_score:
            return self.home_team
        elif self.away_team_score > self.home_team_score:
            return self.away_team
        else:
            return None  # Tie (shouldn't happen in NHL)


class TVBroadcast(models.Model):
    """TV Broadcast information for games"""
    MARKET_CHOICES = [
        ('H', 'Home'),
        ('A', 'Away'),
        ('N', 'National'),
    ]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='tv_broadcasts')
    broadcast_id = models.IntegerField()
    market = models.CharField(max_length=1, choices=MARKET_CHOICES)
    country_code = models.CharField(max_length=2)
    network = models.CharField(max_length=50)
    sequence_number = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['game', 'broadcast_id']
        ordering = ['sequence_number']

    def __str__(self):
        return f"{self.network} ({self.get_market_display()}) - {self.game}"


class GameFetchLog(models.Model):
    """Log of API fetch attempts"""
    fetch_date = models.DateField()
    fetch_datetime = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    games_processed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    api_url = models.URLField()

    class Meta:
        ordering = ['-fetch_datetime']

    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"{self.fetch_date} - {status} ({self.games_processed} games)"