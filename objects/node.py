# objects/node.py
import tkinter as tk
import uuid
from constants import COLORS, BASE_NODE_WIDTH, BASE_NODE_HEIGHT, BASE_FONT_SIZE

class LogicNode:
    """
    Represents a single block (Question, Problem, etc.) on the canvas.
    """
    def __init__(self, app, x, y, node_type, text="New Node", node_id=None):
        self.app = app
        self.node_type = node_type
        self.text = text
        self.references = [] # Stores list of dictionaries for bibliography
        self.x = x
        self.y = y
        # Use provided ID (loading from XML) or generate new unique ID
        self.id = node_id if node_id else str(uuid.uuid4())
        
        # Canvas Item IDs
        self.rect_id = None
        self.text_id = None
        self.type_id = None
        
        self.draw()

    def draw(self):
        """Renders the node on the canvas based on current Zoom level."""
        z = self.app.zoom_level
        w = BASE_NODE_WIDTH * z
        h = BASE_NODE_HEIGHT * z
        f_size = int(BASE_FONT_SIZE * z)
        
        color = COLORS.get(self.node_type, "white")
        
        # Main Box
        self.rect_id = self.app.canvas.create_rectangle(
            self.x, self.y, self.x + w, self.y + h,
            fill=color, outline="black", width=1, tags="node"
        )
        
        # Text Content (Truncated for display)
        disp_text = self.text if len(self.text) < 25 else self.text[:22] + "..."
        self.text_id = self.app.canvas.create_text(
            self.x + w/2, self.y + h/2,
            text=disp_text, width=w-10, 
            font=("Arial", f_size), tags=("node", "text_content")
        )
        
        # Type Label (Small text at top)
        self.type_id = self.app.canvas.create_text(
            self.x + w/2, self.y + (10 * z),
            text=f"[{self.node_type}]", font=("Arial", int(f_size*0.8), "bold"), 
            fill="#555", tags=("node", "text_label")
        )

    def get_center(self):
        """Returns (x, y) of the node's center."""
        coords = self.app.canvas.coords(self.rect_id)
        if not coords: return (self.x, self.y)
        return ((coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2)

    def get_anchor(self, side):
        """
        Returns (x, y) coordinates for a specific side (Top, Bottom, Left, Right).
        Used by Smart Arrows to snap correctly.
        """
        coords = self.app.canvas.coords(self.rect_id)
        if not coords: return (self.x, self.y)
        x1, y1, x2, y2 = coords
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        
        if side == "Top": return (cx, y1)
        if side == "Bottom": return (cx, y2)
        if side == "Left": return (x1, cy)
        if side == "Right": return (x2, cy)
        return (cx, cy)

    def move(self, dx, dy):
        """Updates internal position and moves visual elements."""
        self.x += dx
        self.y += dy
        for item in [self.rect_id, self.text_id, self.type_id]:
            self.app.canvas.move(item, dx, dy)
        # Notify app to redraw connected arrows
        self.app.update_connections(self)

    def set_selected(self, selected=True):
        color = COLORS["Selected"] if selected else "black"
        width = 2 if selected else 1
        self.app.canvas.itemconfig(self.rect_id, outline=color, width=width)

    def update_visuals(self):
        """Refreshes text and color if properties change."""
        disp_text = self.text if len(self.text) < 25 else self.text[:22] + "..."
        self.app.canvas.itemconfig(self.text_id, text=disp_text)
        color = COLORS.get(self.node_type, "white")
        self.app.canvas.itemconfig(self.rect_id, fill=color)
        self.app.canvas.itemconfig(self.type_id, text=f"[{self.node_type}]")