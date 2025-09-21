from django.contrib import admin
from .models import Game


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = [
        'game_id', 
        'game_date', 
        'away_team_abbreviation', 
        'home_team_abbreviation', 
        'game_state',
        'score_display',
        'season'
    ]
    list_filter = [
        'game_state', 
        'game_type', 
        'season', 
        'game_date',
        'neutral_site'
    ]
    search_fields = [
        'home_team_name', 
        'away_team_name', 
        'home_team_abbreviation',
        'away_team_abbreviation',
        'venue_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'winner', 'score_display']
    date_hierarchy = 'game_date'
    ordering = ['-game_date', '-start_time_utc']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'game_id', 
                'season', 
                'game_type', 
                'game_date'
            )
        }),
        ('Away Team', {
            'fields': (
                'away_team_id',
                'away_team_name',
                'away_team_abbreviation',
                'away_team_score',
                'away_team_sog',
                'away_team_record',
                'away_team_logo_url'
            )
        }),
        ('Home Team', {
            'fields': (
                'home_team_id',
                'home_team_name',
                'home_team_abbreviation',
                'home_team_score',
                'home_team_sog',
                'home_team_record',
                'home_team_logo_url'
            )
        }),
        ('Venue & Timing', {
            'fields': (
                'venue_name',
                'start_time_utc',
                'eastern_utc_offset',
                'venue_utc_offset', 
                'venue_timezone',
                'neutral_site'
            )
        }),
        ('Game Status', {
            'fields': (
                'game_state',
                'game_schedule_state'
            )
        }),
        ('Game Results', {
            'fields': (
                'score_display',
                'winner'
            )
        }),
        ('Links', {
            'fields': (
                'game_center_link',
                'tickets_link'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at'
            )
        }),
    )

    def score_display(self, obj):
        return obj.score_display
    score_display.short_description = "Score"

    def winner(self, obj):
        winner = obj.winner
        if winner:
            return winner
        return "No winner" if obj.is_final else "Game not final"
    winner.short_description = "Winner"