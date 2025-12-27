# constants.py

# --- Application Info ---
TITLE = "Thesis Flow"
VERSION = (1, 2, 4)
DESCRIPTION = "A Logic Map Tool for Research Papers."

# --- Visual Dimensions ---
BASE_NODE_WIDTH = 150
BASE_NODE_HEIGHT = 60
BASE_FONT_SIZE = 9

# --- Color Palette ---
COLORS = {
"Question": "#e1f5fe",    # Light Blue
    "Problem": "#ffebee",     # Light Red
    "Solution": "#e8f5e9",    # Light Green
    "Explanation": "#fff3e0", # Light Orange
    "Conclusion": "#f3e5f5",  # <--- ADD THIS (Light Purple)
    
    "Selected": "#0078D7",    # Deep Blue Border when selected
    "Handle": "#FF9500",      # Orange Resize Grip [Image of Resize Grip]
    "LineDefault": "black",
    "LineSelected": "red"
}
ATTACHMENT_DIR = "journal_files"
ICO_PATH = "logo.ico"