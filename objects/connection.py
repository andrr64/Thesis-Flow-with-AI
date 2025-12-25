# objects/connection.py
import tkinter as tk
from constants import COLORS

class Connection:
    """
    Represents a directional link (Arrow) between two nodes.
    It dynamically calculates start/end points based on relative positions.
    """
    def __init__(self, app, parent_node, child_node):
        self.app = app
        self.parent = parent_node
        self.child = child_node
        self.line_id = None
        self.draw()

    def draw(self):
        """Calculates geometry to connect the closest sides of parent and child."""
        # 1. Get centers of both nodes
        pcx, pcy = self.parent.get_center()
        ccx, ccy = self.child.get_center()
        
        # 2. Calculate distance vector
        dx = ccx - pcx
        dy = ccy - pcy
        
        px, py = 0, 0
        cx, cy = 0, 0
        
        # 3. Determine Anchor Points (Smart Routing)
        # If horizontal distance is larger, connect Left/Right sides.
        # Otherwise, connect Top/Bottom sides.
        if abs(dx) > abs(dy):
            # Horizontal connection
            if dx > 0: # Child is to the RIGHT of Parent
                px, py = self.parent.get_anchor("Right")
                cx, cy = self.child.get_anchor("Left")
            else:      # Child is to the LEFT of Parent
                px, py = self.parent.get_anchor("Left")
                cx, cy = self.child.get_anchor("Right")
        else:
            # Vertical connection
            if dy > 0: # Child is BELOW Parent
                px, py = self.parent.get_anchor("Bottom")
                cx, cy = self.child.get_anchor("Top")
            else:      # Child is ABOVE Parent
                px, py = self.parent.get_anchor("Top")
                cx, cy = self.child.get_anchor("Bottom")
        
        # 4. Draw or Update the Line on Canvas
        if self.line_id is None:
            self.line_id = self.app.canvas.create_line(
                px, py, cx, cy,
                arrow=tk.LAST, width=2, fill=COLORS["LineDefault"], 
                tags="connection", activefill="blue" # Highlights blue on hover
            )
        else:
            self.app.canvas.coords(self.line_id, px, py, cx, cy)
            
    def set_selected(self, selected=True):
        """Visual feedback when arrow is clicked."""
        color = COLORS["LineSelected"] if selected else COLORS["LineDefault"]
        width = 4 if selected else 2 # Make it thicker when selected
        self.app.canvas.itemconfig(self.line_id, fill=color, width=width)

    def delete(self):
        """Remove arrow from canvas."""
        self.app.canvas.delete(self.line_id)