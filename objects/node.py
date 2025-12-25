# objects/node.py
import tkinter as tk
import uuid
from constants import COLORS, BASE_NODE_WIDTH, BASE_NODE_HEIGHT, BASE_FONT_SIZE

class LogicNode:
    def __init__(self, app, x, y, node_type, text="New Node", node_id=None, width=None, height=None):
        self.app = app
        self.node_type = node_type
        self.text = text
        self.references = [] 
        self.x = x
        self.y = y
        
        # Base Dimensions (at Zoom 1.0)
        self.width = int(width) if width else BASE_NODE_WIDTH
        self.height = int(height) if height else BASE_NODE_HEIGHT
        
        self.id = node_id if node_id else str(uuid.uuid4())
        
        # Canvas Item IDs
        self.rect_id = None
        self.text_id = None
        self.type_id = None
        self.handle_id = None 
        
        self.draw()

    def draw(self):
        z = self.app.zoom_level
        w = self.width * z
        h = self.height * z
        f_size = int(BASE_FONT_SIZE * z)
        
        color = COLORS.get(self.node_type, "white")
        
        self.rect_id = self.app.canvas.create_rectangle(
            self.x, self.y, self.x + w, self.y + h,
            fill=color, outline="black", width=1, tags=("node", self.id)
        )
        
        disp_text = self.text if len(self.text) < 25 else self.text[:22] + "..."
        self.text_id = self.app.canvas.create_text(
            self.x + w/2, self.y + h/2,
            text=disp_text, width=w-10, 
            font=("Arial", f_size), tags=("node", "text_content", self.id)
        )
        
        self.type_id = self.app.canvas.create_text(
            self.x + w/2, self.y + (10 * z),
            text=f"[{self.node_type}]", font=("Arial", int(f_size*0.8), "bold"), 
            fill="#555", tags=("node", "text_label", self.id)
        )

    def sync_coords(self):
        """CRITICAL FIX: Updates internal x,y to match actual canvas position."""
        coords = self.app.canvas.coords(self.rect_id)
        if coords:
            self.x = coords[0]
            self.y = coords[1]
            # We don't update self.width/height here because those are Base Units.
            # Visual width is coords[2] - coords[0], which is self.width * zoom.

    def draw_handle(self):
        """Draws the resize grip."""
        if self.handle_id:
            self.app.canvas.delete(self.handle_id)
            
        z = self.app.zoom_level
        w = self.width * z
        h = self.height * z
        size = 10 * z 
        
        self.handle_id = self.app.canvas.create_rectangle(
            self.x + w - size, self.y + h - size,
            self.x + w, self.y + h,
            fill=COLORS["Handle"], outline="black", tags=("resize_grip", self.id)
        )

    def resize(self, new_width, new_height):
        # Enforce minimum size
        self.width = max(60, int(new_width))
        self.height = max(40, int(new_height))
        
        z = self.app.zoom_level
        w = self.width * z
        h = self.height * z
        
        # Redraw Main Box using CURRENT synced X/Y
        self.app.canvas.coords(self.rect_id, self.x, self.y, self.x + w, self.y + h)
        
        # Reposition Text
        self.app.canvas.coords(self.text_id, self.x + w/2, self.y + h/2)
        self.app.canvas.itemconfig(self.text_id, width=w-10) 
        
        # Reposition Label
        self.app.canvas.coords(self.type_id, self.x + w/2, self.y + (10 * z))
        
        if self.handle_id:
            self.draw_handle()
            
        self.app.update_connections(self)

    def set_selected(self, selected=True):
        color = COLORS["Selected"] if selected else "black"
        width = 2 if selected else 1
        self.app.canvas.itemconfig(self.rect_id, outline=color, width=width)
        
        if selected:
            self.sync_coords() # Ensure handle draws at correct spot
            self.draw_handle()
        else:
            if self.handle_id:
                self.app.canvas.delete(self.handle_id)
                self.handle_id = None

    def get_center(self):
        coords = self.app.canvas.coords(self.rect_id)
        if not coords: return (self.x, self.y)
        return ((coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2)

    def get_anchor(self, side):
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
        # Visual move
        for item in [self.rect_id, self.text_id, self.type_id]:
            self.app.canvas.move(item, dx, dy)
        if self.handle_id:
            self.app.canvas.move(self.handle_id, dx, dy)
        
        # Sync internal state immediately
        self.x += dx
        self.y += dy
        
        self.app.update_connections(self)

    def update_visuals(self):
        disp_text = self.text if len(self.text) < 25 else self.text[:22] + "..."
        self.app.canvas.itemconfig(self.text_id, text=disp_text)
        color = COLORS.get(self.node_type, "white")
        self.app.canvas.itemconfig(self.rect_id, fill=color)
        self.app.canvas.itemconfig(self.type_id, text=f"[{self.node_type}]")