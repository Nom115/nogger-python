"""
Colour management for Nogger logging system.
Provides ANSI colour codes and colour scheme management.
"""

from enum import Enum
from typing import Dict, Optional


class ColourCodes:
    """ANSI colour codes for terminal output"""
    
    # Reset and formatting
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    # Standard colours
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colours
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background colours
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


class ColourScheme(Enum):
    """Predefined colour schemes for different use cases"""
    
    DEFAULT = "default"
    MINIMAL = "minimal" 
    VIBRANT = "vibrant"
    MONOCHROME = "monochrome"
    DARK_THEME = "dark_theme"
    LIGHT_THEME = "light_theme"


class ColourManager:
    """Manages colour schemes and colour application for log levels"""
    
    def __init__(self, colours_enabled: bool = True, scheme: ColourScheme = ColourScheme.DEFAULT):
        self.colours_enabled = colours_enabled
        self.current_scheme = scheme
        self._schemes = self._initialise_colour_schemes()
    
    def _initialise_colour_schemes(self) -> Dict[ColourScheme, Dict[str, str]]:
        """Initialise predefined colour schemes"""
        # Define LogLevel enum values as strings to avoid circular import
        DEBUG, INFO, WARNING, ERROR, CRITICAL = "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        
        return {
            ColourScheme.DEFAULT: {
                DEBUG: ColourCodes.BRIGHT_BLACK,
                INFO: ColourCodes.BLUE,
                WARNING: ColourCodes.YELLOW,
                ERROR: ColourCodes.RED,
                CRITICAL: ColourCodes.BRIGHT_RED + ColourCodes.BOLD,
                'core': ColourCodes.CYAN,
                'timestamp': ColourCodes.DIM,
            },
            
            ColourScheme.MINIMAL: {
                DEBUG: "",
                INFO: "",
                WARNING: ColourCodes.YELLOW,
                ERROR: ColourCodes.RED,
                CRITICAL: ColourCodes.BRIGHT_RED,
                'core': "",
                'timestamp': ColourCodes.DIM,
            },
            
            ColourScheme.VIBRANT: {
                DEBUG: ColourCodes.BRIGHT_MAGENTA,
                INFO: ColourCodes.BRIGHT_GREEN,
                WARNING: ColourCodes.BRIGHT_YELLOW + ColourCodes.BOLD,
                ERROR: ColourCodes.BRIGHT_RED + ColourCodes.BOLD,
                CRITICAL: ColourCodes.BG_RED + ColourCodes.BRIGHT_WHITE + ColourCodes.BOLD,
                'core': ColourCodes.BRIGHT_CYAN + ColourCodes.BOLD,
                'timestamp': ColourCodes.BRIGHT_BLACK,
            },
            
            ColourScheme.MONOCHROME: {
                DEBUG: "",
                INFO: "",
                WARNING: "",
                ERROR: "",
                CRITICAL: ColourCodes.BOLD,
                'core': "",
                'timestamp': "",
            },
            
            ColourScheme.DARK_THEME: {
                DEBUG: ColourCodes.BRIGHT_BLACK,
                INFO: ColourCodes.BRIGHT_BLUE,
                WARNING: ColourCodes.BRIGHT_YELLOW,
                ERROR: ColourCodes.BRIGHT_RED,
                CRITICAL: ColourCodes.BG_RED + ColourCodes.BRIGHT_WHITE,
                'core': ColourCodes.BRIGHT_CYAN,
                'timestamp': ColourCodes.BRIGHT_BLACK,
            },
            
            ColourScheme.LIGHT_THEME: {
                DEBUG: ColourCodes.DIM,
                INFO: ColourCodes.BLUE,
                WARNING: ColourCodes.YELLOW + ColourCodes.BOLD,
                ERROR: ColourCodes.RED + ColourCodes.BOLD,
                CRITICAL: ColourCodes.RED + ColourCodes.BG_YELLOW + ColourCodes.BOLD,
                'core': ColourCodes.MAGENTA,
                'timestamp': ColourCodes.DIM,
            },
        }
    
    def set_scheme(self, scheme: ColourScheme) -> None:
        """Set the active colour scheme"""
        self.current_scheme = scheme
    
    def get_colour_for_level(self, level) -> str:
        """Get colour code for a specific log level"""
        if not self.colours_enabled:
            return ""
        
        scheme_colours = self._schemes.get(self.current_scheme, self._schemes[ColourScheme.DEFAULT])
        return scheme_colours.get(level, "")
    
    def get_colour_for_element(self, element: str) -> str:
        """Get colour code for a specific element (core, timestamp, etc.)"""
        if not self.colours_enabled:
            return ""
        
        scheme_colours = self._schemes.get(self.current_scheme, self._schemes[ColourScheme.DEFAULT])
        return scheme_colours.get(element, "")
    
    def apply_colour(self, text: str, colour_code: str) -> str:
        """Apply colour to text if colours are enabled"""
        if not self.colours_enabled or not colour_code:
            return text
        return f"{colour_code}{text}{ColourCodes.RESET}"
    
    def enable_colours(self) -> None:
        """Enable colour output"""
        self.colours_enabled = True
    
    def disable_colours(self) -> None:
        """Disable colour output"""
        self.colours_enabled = False
    
    def toggle_colours(self) -> bool:
        """Toggle colour output and return new state"""
        self.colours_enabled = not self.colours_enabled
        return self.colours_enabled
    
    def set_custom_colour_scheme(self, custom_colours: Dict) -> None:
        """Set a custom colour scheme"""
        self._schemes[ColourScheme.DEFAULT] = custom_colours
        self.current_scheme = ColourScheme.DEFAULT