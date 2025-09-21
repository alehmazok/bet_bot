"""
Template loader utility for Telegram bot responses.
Provides Django-style template rendering for bot messages.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
from django.conf import settings
from django.template import Template, Context


class BotTemplateLoader:
    """Template loader for bot responses."""
    
    def __init__(self):
        """Initialize the template loader."""
        self.template_dir = Path(__file__).parent / "templates" / "telegram_bot"
    
    def load_template(self, template_name: str) -> str:
        """
        Load a template file and return its content.
        
        Args:
            template_name: Name of the template file (without .txt extension)
            
        Returns:
            Template content as string
            
        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        template_path = self.template_dir / f"{template_name}.txt"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found at {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def render_template(self, template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Load and render a template with the given context.
        
        Args:
            template_name: Name of the template file (without .txt extension)
            context: Dictionary of variables to use in template rendering
            
        Returns:
            Rendered template as string
        """
        template_content = self.load_template(template_name)
        context = context or {}
        
        # Use Django's template engine for rendering
        template = Template(template_content)
        return template.render(Context(context))
    
    def render_schedule_message(self, games: list, current_date: str) -> str:
        """
        Render the complete schedule message using templates.
        
        Args:
            games: List of game objects
            current_date: Current date string
            
        Returns:
            Complete schedule message
        """
        if not games:
            return self.render_template("schedule_empty")
        
        # Start with header
        header = self.render_template("schedule_header", {"current_date": current_date})
        
        # Add game items
        game_lines = []
        for i, game in enumerate(games):
            game_line = self.render_template("schedule_game_item", {
                "game_number": i + 1,
                "away_team": game.away_team_abbreviation,
                "home_team": game.home_team_abbreviation,
                "game_time": game.start_time_utc.strftime("%H:%M UTC")
            })
            game_lines.append(game_line)
        
        return header + "\n" + "\n".join(game_lines)


# Global template loader instance
template_loader = BotTemplateLoader()