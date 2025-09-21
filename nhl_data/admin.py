from django.contrib import admin
from .models import Team, Venue, Game, TVBroadcast, GameFetchLog


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'abbreviation', 'team_id', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'abbreviation']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['name', 'timezone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']


class TVBroadcastInline(admin.TabularInline):
    model = TVBroadcast
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = [
        'game_id', 
        'game_date', 
        'away_team', 
        'home_team', 
        'game_state',
        'away_team_score',
        'home_team_score',
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
        'home_team__name', 
        'away_team__name', 
        'venue__name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'winner']
    date_hierarchy = 'game_date'
    ordering = ['-game_date', '-start_time_utc']
    inlines = [TVBroadcastInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'game_id', 
                'season', 
                'game_type', 
                'game_date'
            )
        }),
        ('Teams & Venue', {
            'fields': (
                'away_team', 
                'home_team', 
                'venue', 
                'neutral_site'
            )
        }),
        ('Timing', {
            'fields': (
                'start_time_utc',
                'eastern_utc_offset',
                'venue_utc_offset', 
                'venue_timezone'
            )
        }),
        ('Game Status', {
            'fields': (
                'game_state',
                'game_schedule_state'
            )
        }),
        ('Scores & Stats', {
            'fields': (
                'away_team_score',
                'home_team_score',
                'away_team_sog',
                'home_team_sog',
                'winner'
            )
        }),
        ('Team Records', {
            'fields': (
                'away_team_record',
                'home_team_record'
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

    def winner(self, obj):
        winner = obj.winner
        if winner:
            return f"{winner.name} ({winner.abbreviation})"
        return "No winner" if obj.is_final else "Game not final"
    winner.short_description = "Winner"


@admin.register(TVBroadcast)
class TVBroadcastAdmin(admin.ModelAdmin):
    list_display = [
        'game', 
        'network', 
        'market', 
        'country_code',
        'sequence_number'
    ]
    list_filter = ['market', 'country_code', 'network']
    search_fields = ['network', 'game__away_team__name', 'game__home_team__name']
    readonly_fields = ['created_at']
    ordering = ['game__game_date', 'sequence_number']


@admin.register(GameFetchLog)
class GameFetchLogAdmin(admin.ModelAdmin):
    list_display = [
        'fetch_date', 
        'fetch_datetime', 
        'success', 
        'games_processed',
        'api_url'
    ]
    list_filter = ['success', 'fetch_date']
    search_fields = ['api_url', 'error_message']
    readonly_fields = ['fetch_datetime']
    date_hierarchy = 'fetch_date'
    ordering = ['-fetch_datetime']
    
    fieldsets = (
        ('Fetch Information', {
            'fields': (
                'fetch_date',
                'fetch_datetime',
                'api_url'
            )
        }),
        ('Results', {
            'fields': (
                'success',
                'games_processed',
                'error_message'
            )
        }),
    )

    def has_add_permission(self, request):
        # Prevent manual creation of fetch logs
        return False