# constants.py

# --- Visual Dimensions ---
BASE_NODE_WIDTH = 150
BASE_NODE_HEIGHT = 60
BASE_FONT_SIZE = 9

# --- Color Palette (Classic System Colors) ---
COLORS = {
    # Node Types
    "Question": "#ADD8E6",    # Light Blue
    "Problem": "#FFDAB9",     # Peach/Orange
    "Solution": "#90EE90",    # Light Green
    "Explanation": "#D3D3D3", # Light Grey
    
    # State Colors
    "Selected": "#FF0000",    # Red Border when selected
    "LineDefault": "black",   # Default Arrow Color
    "LineSelected": "red"     # Selected Arrow Color
}

TITLE = "Thesis Flow"
DESCRIPTION = """
A Logic Map Tool for Research Papers.
Created by Derza Andreas.
"""
VERSION = [1, 0, 0] # major, minor, patch