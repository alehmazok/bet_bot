from django.db import models
from django.utils import timezone


class Game(models.Model):
    """NHL Game model - stores complete game information"""
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
    
    # Home Team Info
    home_team_id = models.IntegerField(help_text="Home team NHL API ID")
    home_team_name = models.CharField(max_length=100, help_text="Home team name")
    home_team_abbreviation = models.CharField(max_length=5, help_text="Home team abbreviation")
    home_team_score = models.IntegerField(null=True, blank=True, help_text="Home team score")
    home_team_sog = models.IntegerField(null=True, blank=True, help_text="Home team shots on goal")
    home_team_record = models.CharField(max_length=20, blank=True, null=True, help_text="Home team record")
    home_team_logo_url = models.URLField(blank=True, null=True, help_text="Home team logo URL")
    
    # Away Team Info
    away_team_id = models.IntegerField(help_text="Away team NHL API ID")
    away_team_name = models.CharField(max_length=100, help_text="Away team name")
    away_team_abbreviation = models.CharField(max_length=5, help_text="Away team abbreviation")
    away_team_score = models.IntegerField(null=True, blank=True, help_text="Away team score")
    away_team_sog = models.IntegerField(null=True, blank=True, help_text="Away team shots on goal")
    away_team_record = models.CharField(max_length=20, blank=True, null=True, help_text="Away team record")
    away_team_logo_url = models.URLField(blank=True, null=True, help_text="Away team logo URL")
    
    # Venue and timing
    venue_name = models.CharField(max_length=200, blank=True, null=True, help_text="Venue name")
    start_time_utc = models.DateTimeField(help_text="Game start time in UTC")
    eastern_utc_offset = models.CharField(max_length=10, blank=True, null=True)
    venue_utc_offset = models.CharField(max_length=10, blank=True, null=True)
    venue_timezone = models.CharField(max_length=50, blank=True, null=True)
    
    # Game state
    game_state = models.CharField(max_length=10, choices=GAME_STATES)
    game_schedule_state = models.CharField(max_length=20, default='OK')
    neutral_site = models.BooleanField(default=False)
    
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
        return f"{self.away_team_abbreviation} @ {self.home_team_abbreviation} ({self.game_date})"

    @property
    def is_final(self):
        return self.game_state in ['FINAL', 'OFF']

    @property
    def winner(self):
        """Returns the winning team abbreviation if game is final"""
        if not self.is_final or self.home_team_score is None or self.away_team_score is None:
            return None
        
        if self.home_team_score > self.away_team_score:
            return self.home_team_abbreviation
        elif self.away_team_score > self.home_team_score:
            return self.away_team_abbreviation
        else:
            return None  # Tie (shouldn't happen in NHL)

    @property
    def score_display(self):
        """Returns formatted score display"""
        if self.away_team_score is not None and self.home_team_score is not None:
            return f"{self.away_team_abbreviation} {self.away_team_score} - {self.home_team_score} {self.home_team_abbreviation}"
        return f"{self.away_team_abbreviation} @ {self.home_team_abbreviation}"