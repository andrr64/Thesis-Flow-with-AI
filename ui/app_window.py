# ui/app_window.py
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import xml.etree.ElementTree as ET
import uuid
import constants

# Import internal modules
from constants import COLORS, BASE_FONT_SIZE
from objects.node import LogicNode
from objects.connection import Connection

class ThesisFlowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Thesis Flow 1.1.0") 
        self.root.geometry("1400x800")
        
        # --- App State ---
        self.nodes = []           # List of LogicNode objects
        self.connections = []     # List of Connection objects
        self.selected_object = None 
        
        self.zoom_level = 1.0
        self.drag_data = {"item": None, "x": 0, "y": 0}
        self.connect_mode = False
        self.connect_source = None

        # --- Initialization ---
        self.setup_menu()
        self.setup_ui()
        self.bind_shortcuts()

    def bind_shortcuts(self):
        # Global Save
        self.root.bind("<Control-s>", lambda e: self.save_to_xml())
        # Delete Key (Windows/Linux usually Delete, Mac sometimes BackSpace)
        self.root.bind("<Delete>", lambda e: self.delete_selected_object())
        self.root.bind("<BackSpace>", lambda e: self.delete_selected_object())

    # -------------------------------------------------------------------------
    # UI SETUP
    # -------------------------------------------------------------------------
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open XML...", command=self.load_from_xml)
        file_menu.add_command(label="Save XML (Ctrl+S)", command=self.save_to_xml)
        file_menu.add_separator()
        file_menu.add_command(label="Export Bibliography", command=self.show_global_references)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # About Menu
        about_menu = tk.Menu(menubar, tearoff=0)
        about_menu.add_command(label="About Thesis Flow", command=self.show_about)
        menubar.add_cascade(label="About", menu=about_menu)

        self.root.config(menu=menubar)

    def setup_ui(self):
        # 1. Top Toolbar
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        tk.Button(toolbar, text="Center View", command=self.center_view).pack(side=tk.LEFT, padx=5, pady=2)
        tk.Label(toolbar, text=" | Tip: Press DELETE to remove selected Arrows/Nodes").pack(side=tk.LEFT, padx=5)

        # 2. Main Layout Split (Canvas vs Properties)
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=4, bg="#d9d9d9")
        self.paned.pack(fill=tk.BOTH, expand=True)

        # 3. Left Side: Canvas
        left_frame = tk.Frame(self.paned)
        self.canvas = tk.Canvas(left_frame, bg="white", scrollregion=(-10000, -10000, 10000, 10000))
        
        # Scrollbars
        h_scroll = tk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scroll = tk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.paned.add(left_frame, minsize=800)

        self._draw_grid()
        self.bind_canvas_events()
        self.center_view()

        # 4. Right Side: Properties Panel
        self.right_panel = tk.Frame(self.paned, bd=2, relief=tk.SUNKEN, padx=5, pady=5)
        self.paned.add(self.right_panel, minsize=350)
        
        self.setup_right_panel()

    def setup_right_panel(self):
        # -- Section 1: Node Properties --
        sec1 = tk.LabelFrame(self.right_panel, text="Node Properties", padx=5, pady=5)
        sec1.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(sec1, text="Type:").pack(anchor="w")
        self.var_type = tk.StringVar()
        self.cb_type = ttk.Combobox(sec1, textvariable=self.var_type, values=list(COLORS.keys())[:4], state="readonly")
        self.cb_type.pack(fill=tk.X, pady=2)
        
        tk.Label(sec1, text="Argument / Text:").pack(anchor="w")
        self.txt_argument = tk.Text(sec1, height=4, width=30)
        self.txt_argument.pack(fill=tk.X, pady=2)
        # Binds Ctrl+S inside text box to save properties
        self.txt_argument.bind("<Control-s>", lambda e: self.save_node_details())
        
        btn_box = tk.Frame(sec1)
        btn_box.pack(fill=tk.X, pady=5)
        tk.Button(btn_box, text="Save / Apply (Ctrl+S)", command=self.save_node_details, bg="#dddddd").pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(btn_box, text="Delete Item", command=self.delete_selected_object, bg="#ffcccc").pack(side=tk.RIGHT)

        # -- Section 2: Reference List (Treeview) --
        sec2 = tk.LabelFrame(self.right_panel, text="Reference List", padx=5, pady=5)
        sec2.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("title", "link")
        self.ref_tree = ttk.Treeview(sec2, columns=columns, show="headings", height=6)
        self.ref_tree.heading("title", text="Title")
        self.ref_tree.heading("link", text="Link")
        self.ref_tree.column("title", width=120)
        self.ref_tree.column("link", width=180)
        
        sb = tk.Scrollbar(sec2, orient=tk.VERTICAL, command=self.ref_tree.yview)
        self.ref_tree.configure(yscrollcommand=sb.set)
        
        self.ref_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.ref_tree.bind("<<TreeviewSelect>>", self.on_ref_select)

        # -- Section 3: Reference Details --
        sec3 = tk.LabelFrame(self.right_panel, text="Reference Details", padx=5, pady=5)
        sec3.pack(fill=tk.X)
        
        tk.Label(sec3, text="Title (Optional):").pack(anchor="w")
        self.ent_ref_title = tk.Entry(sec3)
        self.ent_ref_title.pack(fill=tk.X, pady=2)
        
        tk.Label(sec3, text="Link / DOI (Required):").pack(anchor="w")
        self.ent_ref_link = tk.Entry(sec3)
        self.ent_ref_link.pack(fill=tk.X, pady=2)
        
        tk.Label(sec3, text="Description (Optional):").pack(anchor="w")
        self.txt_ref_desc = tk.Text(sec3, height=3, width=30)
        self.txt_ref_desc.pack(fill=tk.X, pady=2)
        
        tk.Button(sec3, text="Add / Update Reference", command=self.save_reference).pack(fill=tk.X, pady=5)
        tk.Button(sec3, text="Remove Selected Ref", command=self.remove_reference).pack(fill=tk.X)

        self.disable_all_panels()

    def _draw_grid(self):
        """Draws a large faint grid for visual guidance."""
        for i in range(-10000, 10000, 100):
            self.canvas.create_line(i, -10000, i, 10000, fill="#f0f0f0", width=1)
            self.canvas.create_line(-10000, i, 10000, i, fill="#f0f0f0", width=1)
        # Origin lines
        self.canvas.create_line(0, -10000, 0, 10000, fill="#d0d0d0", width=2)
        self.canvas.create_line(-10000, 0, 10000, 0, fill="#d0d0d0", width=2)

    def bind_canvas_events(self):
        self.canvas.bind("<Button-3>", self.context_menu)
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_drop)
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.pan_move)
        self.canvas.bind("<Control-MouseWheel>", self.do_zoom)

    # -------------------------------------------------------------------------
    # CANVAS LOGIC (Zoom/Pan/Updates)
    # -------------------------------------------------------------------------
    def center_view(self):
        self.canvas.xview_moveto(0.5)
        self.canvas.yview_moveto(0.5)

    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def pan_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def do_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        new_zoom = self.zoom_level * factor
        # Limit zoom
        if 0.2 < new_zoom < 3.0:
            self.canvas.scale("all", self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), factor, factor)
            self.zoom_level = new_zoom
            
            # Rescale Fonts
            new_fs = int(BASE_FONT_SIZE * self.zoom_level)
            for t in self.canvas.find_withtag("text_content"): self.canvas.itemconfig(t, font=("Arial", new_fs))
            for t in self.canvas.find_withtag("text_label"): self.canvas.itemconfig(t, font=("Arial", int(new_fs*0.7), "bold"))
            
            # Redraw smart arrows (positions change on zoom)
            for conn in self.connections: conn.draw()

    def update_connections(self, moved_node):
        """Called by a node when it moves to update attached arrows."""
        for conn in self.connections:
            if conn.parent == moved_node or conn.child == moved_node:
                conn.draw()

    # -------------------------------------------------------------------------
    # SELECTION & INTERACTION
    # -------------------------------------------------------------------------
    def on_canvas_click(self, event):
        # 1. Handle Connection creation mode
        if self.connect_mode and self.connect_source:
            target = self.find_node_at(event.x, event.y)
            if target and target != self.connect_source:
                self.connections.append(Connection(self, self.connect_source, target))
            self.connect_mode = False
            self.connect_source = None
            self.canvas.config(cursor="")
            return

        # 2. Deselect previous
        if self.selected_object:
            self.selected_object.set_selected(False)
            self.selected_object = None
            self.disable_all_panels()

        # 3. Try to select a Node
        node = self.find_node_at(event.x, event.y)
        if node:
            self.select_object(node)
            self.drag_data["item"] = node
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            return

        # 4. Try to select an Arrow (Connection)
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        # High tolerance (10px) to make clicking lines easier
        items = self.canvas.find_overlapping(cx-10, cy-10, cx+10, cy+10)
        for item_id in items:
            tags = self.canvas.gettags(item_id)
            if "connection" in tags:
                for conn in self.connections:
                    if conn.line_id == item_id:
                        self.select_object(conn)
                        return

    def select_object(self, obj):
        self.selected_object = obj
        obj.set_selected(True)
        
        if isinstance(obj, LogicNode):
            self.populate_node_panel(obj)
            self.enable_node_panel()
        elif isinstance(obj, Connection):
            # Arrows don't have properties to edit yet, so disable panel
            self.disable_all_panels()

    def find_node_at(self, sx, sy):
        """Finds if a node exists at screen coordinates sx, sy."""
        cx, cy = self.canvas.canvasx(sx), self.canvas.canvasy(sy)
        for node in self.nodes:
            coords = self.canvas.coords(node.rect_id)
            if coords and coords[0] <= cx <= coords[2] and coords[1] <= cy <= coords[3]:
                return node
        return None

    def on_drag(self, event):
        node = self.drag_data["item"]
        if node and isinstance(node, LogicNode):
            # Calculate movement in Canvas Coordinates
            dx = (event.x - self.drag_data["x"]) / self.zoom_level
            dy = (event.y - self.drag_data["y"]) / self.zoom_level
            node.move(dx, dy)
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def on_drop(self, event):
        self.drag_data["item"] = None

    def context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        node = self.find_node_at(event.x, event.y)
        if node:
            menu.add_command(label="Connect Arrow", command=lambda: self.start_connect(node))
            menu.add_command(label="Delete Node", command=lambda: self.delete_object(node))
        else:
            # Create new nodes
            menu.add_command(label="Add Question", command=lambda: self.add_node("Question", event.x, event.y))
            menu.add_command(label="Add Problem", command=lambda: self.add_node("Problem", event.x, event.y))
            menu.add_command(label="Add Solution", command=lambda: self.add_node("Solution", event.x, event.y))
            menu.add_command(label="Add Explanation", command=lambda: self.add_node("Explanation", event.x, event.y))
        menu.post(event.x_root, event.y_root)

    def start_connect(self, node):
        self.connect_mode = True
        self.connect_source = node
        self.canvas.config(cursor="crosshair")

    # -------------------------------------------------------------------------
    # RIGHT PANEL & DATA LOGIC
    # -------------------------------------------------------------------------
    def populate_node_panel(self, node):
        self.var_type.set(node.node_type)
        self.txt_argument.delete("1.0", tk.END)
        self.txt_argument.insert("1.0", node.text)
        self.refresh_ref_tree(node)
        self.clear_ref_details()

    def refresh_ref_tree(self, node):
        for item in self.ref_tree.get_children():
            self.ref_tree.delete(item)
        for ref in node.references:
            display_title = ref.get('title', '') or "(No Title)"
            self.ref_tree.insert("", tk.END, iid=ref['id'], values=(display_title, ref['link']))

    def on_ref_select(self, event):
        """Loads reference details when a row in Treeview is clicked."""
        selected_id = self.ref_tree.selection()
        if not selected_id: return
        
        ref_id = selected_id[0]
        if isinstance(self.selected_object, LogicNode):
            ref_data = next((r for r in self.selected_object.references if r['id'] == ref_id), None)
            if ref_data:
                self.ent_ref_title.delete(0, tk.END)
                self.ent_ref_title.insert(0, ref_data.get('title', ''))
                self.ent_ref_link.delete(0, tk.END)
                self.ent_ref_link.insert(0, ref_data.get('link', ''))
                self.txt_ref_desc.delete("1.0", tk.END)
                self.txt_ref_desc.insert("1.0", ref_data.get('desc', ''))

    def save_node_details(self, event=None):
        if isinstance(self.selected_object, LogicNode):
            self.selected_object.node_type = self.var_type.get()
            self.selected_object.text = self.txt_argument.get("1.0", tk.END).strip()
            self.selected_object.update_visuals()
            return "break" # Prevent default Ctrl+S printing in text box

    def save_reference(self):
        if not isinstance(self.selected_object, LogicNode): return
        link = self.ent_ref_link.get().strip()
        if not link:
            messagebox.showwarning("Missing Data", "Link field is required.")
            return
        
        title = self.ent_ref_title.get().strip()
        desc = self.txt_ref_desc.get("1.0", tk.END).strip()
        
        sel_id = self.ref_tree.selection()
        if sel_id:
            # Update Existing
            ref_id = sel_id[0]
            for ref in self.selected_object.references:
                if ref['id'] == ref_id:
                    ref['title'] = title
                    ref['link'] = link
                    ref['desc'] = desc
        else:
            # Add New
            new_ref = {'id': str(uuid.uuid4()), 'title': title, 'link': link, 'desc': desc}
            self.selected_object.references.append(new_ref)
        
        self.refresh_ref_tree(self.selected_object)
        self.clear_ref_details()

    def remove_reference(self):
        if not isinstance(self.selected_object, LogicNode): return
        sel_id = self.ref_tree.selection()
        if sel_id:
            ref_id = sel_id[0]
            self.selected_object.references = [r for r in self.selected_object.references if r['id'] != ref_id]
            self.refresh_ref_tree(self.selected_object)
            self.clear_ref_details()

    def clear_ref_details(self):
        self.ent_ref_title.delete(0, tk.END)
        self.ent_ref_link.delete(0, tk.END)
        self.txt_ref_desc.delete("1.0", tk.END)
        if self.ref_tree.selection():
            self.ref_tree.selection_remove(self.ref_tree.selection())

    # --- UI STATE HELPERS ---
    def disable_all_panels(self):
        """Disables all input fields in the right panel."""
        for child in self.right_panel.winfo_children():
            for sub in child.winfo_children():
                try: sub.configure(state='disabled') 
                except: pass

    def enable_node_panel(self):
        """Enables input fields."""
        for child in self.right_panel.winfo_children():
            for sub in child.winfo_children():
                try: sub.configure(state='normal')
                except: pass
        self.cb_type.configure(state="readonly")

    # -------------------------------------------------------------------------
    # OBJECT MANAGEMENT (Add/Delete)
    # -------------------------------------------------------------------------
    def delete_selected_object(self):
        if self.selected_object:
            self.delete_object(self.selected_object)
            self.selected_object = None
            self.disable_all_panels()

    def delete_object(self, obj):
        if isinstance(obj, Connection):
            obj.delete()
            if obj in self.connections: self.connections.remove(obj)
        elif isinstance(obj, LogicNode):
            # Remove visuals
            self.canvas.delete(obj.rect_id)
            self.canvas.delete(obj.text_id)
            self.canvas.delete(obj.type_id)
            
            # Remove connections attached to this node
            to_remove = [c for c in self.connections if c.parent == obj or c.child == obj]
            for c in to_remove:
                c.delete()
                self.connections.remove(c)
                
            if obj in self.nodes: self.nodes.remove(obj)

    def add_node(self, n_type, x, y):
        cx, cy = self.canvas.canvasx(x), self.canvas.canvasy(y)
        node = LogicNode(self, cx, cy, n_type)
        self.nodes.append(node)

    # -------------------------------------------------------------------------
    # PERSISTENCE (XML Save/Load)
    # -------------------------------------------------------------------------
    def save_to_xml(self):
        path = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML", "*.xml")])
        if not path: return
        
        root = ET.Element("ThesisFlow")
        
        # Save Nodes
        for n in self.nodes:
            ne = ET.SubElement(root, "Node", id=n.id, type=n.node_type, x=str(n.x), y=str(n.y))
            ET.SubElement(ne, "Text").text = n.text
            re = ET.SubElement(ne, "References")
            for ref in n.references:
                r_item = ET.SubElement(re, "Ref", id=ref['id'])
                ET.SubElement(r_item, "Title").text = ref.get('title', '')
                ET.SubElement(r_item, "Link").text = ref.get('link', '')
                ET.SubElement(r_item, "Desc").text = ref.get('desc', '')
        
        # Save Connections
        ce_root = ET.SubElement(root, "Connections")
        for c in self.connections:
            ET.SubElement(ce_root, "Link", parent=c.parent.id, child=c.child.id)
            
        try:
            ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
            messagebox.showinfo("Saved", "File saved successfully!")
        except Exception as e: messagebox.showerror("Error", str(e))

    def load_from_xml(self):
        path = filedialog.askopenfilename(filetypes=[("XML", "*.xml")])
        if not path: return
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            
            # Wipe current state
            for n in list(self.nodes): self.delete_object(n)
            
            id_map = {}
            # Load Nodes
            for ne in root.findall("Node"):
                node = LogicNode(self, float(ne.get('x')), float(ne.get('y')), ne.get('type'), node_id=ne.get('id'))
                node.text = ne.find("Text").text or ""
                
                ref_container = ne.find("References")
                if ref_container is not None:
                    for r_xml in ref_container.findall("Ref"):
                        node.references.append({
                            'id': r_xml.get('id', str(uuid.uuid4())),
                            'title': r_xml.find("Title").text or "",
                            'link': r_xml.find("Link").text or "",
                            'desc': r_xml.find("Desc").text or ""
                        })
                node.update_visuals()
                self.nodes.append(node)
                id_map[node.id] = node
            
            # Load Connections
            conn_root = root.find("Connections")
            if conn_root is not None:
                for link in conn_root.findall("Link"):
                    pid, cid = link.get("parent"), link.get("child")
                    if pid in id_map and cid in id_map:
                        self.connections.append(Connection(self, id_map[pid], id_map[cid]))
            
            self.center_view()
        except Exception as e: messagebox.showerror("Error", str(e))

    def show_global_references(self):
        """Generates a simple text-based bibliography."""
        lines = ["--- BIBLIOGRAPHY EXPORT ---", ""]
        for n in self.nodes:
            if n.references:
                lines.append(f"[{n.node_type}] {n.text}")
                for r in n.references:
                    lines.append(f"   • {r['title']} ({r['link']})")
                    if r['desc']: lines.append(f"     Note: {r['desc']}")
                lines.append("")
        
        top = tk.Toplevel(self.root)
        top.geometry("600x500")
        t = tk.Text(top, padx=10, pady=10)
        t.pack(fill=tk.BOTH, expand=True)
        t.insert("1.0", "\n".join(lines))

    def show_about(self):
        messagebox.showinfo("About", f'{constants.TITLE} {constants.VERSION[0]}.{constants.VERSION[1]}.{constants.VERSION[2]}\n\n{constants.DESCRIPTION}')