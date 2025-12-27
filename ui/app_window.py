# ui/app_window.py
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import xml.etree.ElementTree as ET
import uuid
import os
import shutil
import webbrowser
import constants

from constants import COLORS, BASE_FONT_SIZE, BASE_NODE_WIDTH, BASE_NODE_HEIGHT
from objects.node import LogicNode
from objects.connection import Connection

def resource_path(relative_path):
    """Akses resource saat di-pack PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ThesisFlowApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{constants.TITLE} {constants.VERSION[0]}.{constants.VERSION[1]}.{constants.VERSION[2]}") 
        self.root.geometry("1400x800")
        self.icon_path = resource_path(constants.ICO_PATH)
        self.root.iconbitmap(self.icon_path)
        self.nodes = []
        self.connections = []
        self.selected_object = None 
        
        self.project_id = str(uuid.uuid4())
        
        self.zoom_level = 1.0
        self.drag_data = {"item": None, "x": 0, "y": 0, "mode": None}
        self.connect_mode = False
        self.connect_source = None

        self.setup_menu()
        self.setup_ui()
        self.bind_shortcuts()

    def bind_shortcuts(self):
        self.root.bind("<Control-s>", lambda e: self.save_to_xml())
        self.root.bind("<Delete>", lambda e: self.delete_selected_object())

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open XML...", command=self.load_from_xml)
        file_menu.add_command(label="Save XML (Ctrl+S)", command=self.save_to_xml)
        file_menu.add_separator()
        file_menu.add_command(label="Export Bibliography", command=self.show_global_references)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        about_menu = tk.Menu(menubar, tearoff=0)
        about_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="About", menu=about_menu)
        self.root.config(menu=menubar)

    def setup_ui(self):
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        tk.Button(toolbar, text="⌖ Center View", command=self.center_view).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Default Zoom", command=self.reset_zoom).pack(side=tk.LEFT, padx=2, pady=2)
        self.lbl_zoom = tk.Label(toolbar, text="100%", width=5, fg="#555")
        self.lbl_zoom.pack(side=tk.LEFT, padx=2)
        tk.Label(toolbar, text="| Drag Handle to Resize | Middle Click to Pan").pack(side=tk.LEFT, padx=10)

        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=4, bg="#d9d9d9")
        self.paned.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(self.paned)
        self.canvas = tk.Canvas(left_frame, bg="white", scrollregion=(-10000, -10000, 10000, 10000))
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

        self.right_panel = tk.Frame(self.paned, bd=2, relief=tk.SUNKEN, padx=5, pady=5)
        self.paned.add(self.right_panel, minsize=350)
        self.setup_right_panel()

    def setup_right_panel(self):
        # --- SECTION 1: NODE PROPERTIES ---
        sec1 = tk.LabelFrame(self.right_panel, text="Node Properties", padx=5, pady=5)
        sec1.pack(fill=tk.X, pady=(0, 10))
        
        # Grid Layout for Section 1
        tk.Label(sec1, text="Type:").grid(row=0, column=0, sticky="w", pady=2)
        self.var_type = tk.StringVar()
        self.cb_type = ttk.Combobox(sec1, textvariable=self.var_type, values=list(COLORS.keys()), state="readonly", width=15)
        self.cb_type.grid(row=0, column=1, columnspan=2, sticky="ew", pady=2)
        
        tk.Label(sec1, text="Size:").grid(row=1, column=0, sticky="w", pady=2)
        dim_frame = tk.Frame(sec1)
        dim_frame.grid(row=1, column=1, columnspan=2, sticky="w")
        
        self.var_w = tk.IntVar(value=150)
        tk.Entry(dim_frame, textvariable=self.var_w, width=5).pack(side=tk.LEFT)
        tk.Label(dim_frame, text="x").pack(side=tk.LEFT, padx=2)
        self.var_h = tk.IntVar(value=60)
        tk.Entry(dim_frame, textvariable=self.var_h, width=5).pack(side=tk.LEFT)
        tk.Button(dim_frame, text="Set", command=self.apply_manual_size, width=4).pack(side=tk.LEFT, padx=5)

        tk.Label(sec1, text="Text:").grid(row=2, column=0, sticky="nw", pady=2)
        self.txt_argument = tk.Text(sec1, height=3, width=25)
        self.txt_argument.grid(row=2, column=1, columnspan=2, sticky="ew", pady=2)
        self.txt_argument.bind("<Control-s>", lambda e: self.save_node_details())
        
        btn_frame_node = tk.Frame(sec1)
        btn_frame_node.grid(row=3, column=0, columnspan=3, sticky="ew", pady=5)
        tk.Button(btn_frame_node, text="Save Node", command=self.save_node_details, bg="#dddddd").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        tk.Button(btn_frame_node, text="Delete", command=self.delete_selected_object, bg="#ffcccc").pack(side=tk.LEFT)

        sec1.columnconfigure(1, weight=1)

        # --- SECTION 2: REFERENCE LIST ---
        sec2 = tk.LabelFrame(self.right_panel, text="Reference List", padx=5, pady=5)
        sec2.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("title", "link", "file") 
        self.ref_tree = ttk.Treeview(sec2, columns=columns, show="headings", height=5)
        self.ref_tree.heading("title", text="Title")
        self.ref_tree.heading("link", text="Link")
        self.ref_tree.heading("file", text="PDF")
        self.ref_tree.column("title", width=100)
        self.ref_tree.column("link", width=120)
        self.ref_tree.column("file", width=50)
        
        sb = tk.Scrollbar(sec2, orient=tk.VERTICAL, command=self.ref_tree.yview)
        self.ref_tree.configure(yscrollcommand=sb.set)
        
        self.ref_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.ref_tree.bind("<<TreeviewSelect>>", self.on_ref_select)

        # --- SECTION 3: REFERENCE DETAILS ---
        sec3 = tk.LabelFrame(self.right_panel, text="Reference Details", padx=5, pady=5)
        sec3.pack(fill=tk.X)
        
        sec3.columnconfigure(1, weight=1)

        # Row 0
        tk.Label(sec3, text="Title:").grid(row=0, column=0, sticky="w", pady=2)
        self.ent_ref_title = tk.Entry(sec3)
        self.ent_ref_title.grid(row=0, column=1, columnspan=2, sticky="ew", pady=2)

        # Row 1 (Fixed: Removed tooltip arg)
        tk.Label(sec3, text="Link:").grid(row=1, column=0, sticky="w", pady=2)
        self.ent_ref_link = tk.Entry(sec3)
        self.ent_ref_link.grid(row=1, column=1, sticky="ew", pady=2)
        tk.Button(sec3, text="🌐", width=3, command=self.open_link).grid(row=1, column=2, padx=(2,0))

        # Row 2
        tk.Label(sec3, text="PDF:").grid(row=2, column=0, sticky="w", pady=2)
        self.ent_ref_file = tk.Entry(sec3, state='readonly')
        self.ent_ref_file.grid(row=2, column=1, sticky="ew", pady=2)
        
        file_btn_frame = tk.Frame(sec3)
        file_btn_frame.grid(row=2, column=2, sticky="e")
        tk.Button(file_btn_frame, text="📂", width=3, command=self.browse_pdf).pack(side=tk.LEFT, padx=(2, 0))
        tk.Button(file_btn_frame, text="📄", width=3, command=self.open_pdf).pack(side=tk.LEFT, padx=(2, 0))

        # Row 3
        tk.Label(sec3, text="Desc:").grid(row=3, column=0, sticky="nw", pady=2)
        self.txt_ref_desc = tk.Text(sec3, height=3, width=20)
        self.txt_ref_desc.bind("<Control-s>", lambda e: self.save_reference(e))
        self.txt_ref_desc.grid(row=3, column=1, columnspan=2, sticky="ew", pady=2)

        # Row 4
        btn_box_ref = tk.Frame(sec3)
        btn_box_ref.grid(row=4, column=0, columnspan=3, sticky="ew", pady=5)
        
        tk.Button(btn_box_ref, text="+ New", command=self.prepare_new_reference, width=6).pack(side=tk.LEFT, padx=(0, 2))
        tk.Button(btn_box_ref, text="Save / Update", command=self.save_reference, bg="#e6f3ff").pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(btn_box_ref, text="🗑", command=self.remove_reference, width=3, bg="#ffcccc").pack(side=tk.LEFT, padx=(2, 0))

        self.disable_all_panels()

    def open_link(self):
        link = self.ent_ref_link.get().strip()
        if link:
            if not link.startswith("http"):
                link = "https://" + link
            try:
                webbrowser.open(link)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot open link: {e}")

    def prepare_new_reference(self):
        self.clear_ref_details()
        self.ent_ref_title.focus_set()

    def browse_pdf(self):
        if not isinstance(self.selected_object, LogicNode): return
        
        file_path = filedialog.askopenfilename(
            title="Select PDF Reference", 
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                filename = os.path.basename(file_path)
                
                # --- PERUBAHAN 2: Folder berdasarkan Node UUID ---
                # Ambil ID dari node yang sedang dipilih
                node_id = self.selected_object.id
                
                # Buat path: journal_files / {node_id} /
                base_journal_dir = os.path.join(os.getcwd(), "journal_files")
                target_dir = os.path.join(base_journal_dir, node_id)
                
                # Buat folder jika belum ada
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                
                # Set destinasi akhir
                dest_path = os.path.join(target_dir, filename)
                # -------------------------------------------------

                # Copy file
                if os.path.abspath(file_path) != os.path.abspath(dest_path):
                    shutil.copy2(file_path, dest_path)
                
                # Update UI
                self.ent_ref_file.configure(state='normal')
                self.ent_ref_file.delete(0, tk.END)
                self.ent_ref_file.insert(0, filename)
                self.ent_ref_file.configure(state='readonly')
                
            except Exception as e:
                messagebox.showerror("File Error", f"Could not copy file: {e}")
    def open_pdf(self):
        filename = self.ent_ref_file.get()
        if not filename: return
        
        # Pastikan ada node yang dipilih untuk mengambil ID-nya
        if not isinstance(self.selected_object, LogicNode): return

        # --- PERUBAHAN 3: Cari file di dalam folder UUID Node ---
        node_id = self.selected_object.id
        path = os.path.join(os.getcwd(), "journal_files", node_id, filename)
        # -------------------------------------------------------
        
        if os.path.exists(path):
            try:
                os.startfile(path) # Windows
            except AttributeError:
                import subprocess
                subprocess.call(('xdg-open', path)) # Linux/Mac
        else:
            # Fallback: Coba cari di folder root journal_files (untuk kompatibilitas file lama)
            old_path = os.path.join(os.getcwd(), "journal_files", filename)
            if os.path.exists(old_path):
                try:
                    os.startfile(old_path)
                except AttributeError:
                    import subprocess
                    subprocess.call(('xdg-open', old_path))
            else:
                messagebox.showerror("Error", f"File not found in:\n{path}")
                
    def _draw_grid(self):
        for i in range(-10000, 10000, 100):
            self.canvas.create_line(i, -10000, i, 10000, fill="#f0f0f0", width=1)
            self.canvas.create_line(-10000, i, 10000, i, fill="#f0f0f0", width=1)
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
        self.canvas.bind("<Motion>", self.on_mouse_move)

    def center_view(self):
        if not self.nodes:
            self.canvas.xview_moveto(0.5); self.canvas.yview_moveto(0.5); return
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')
        for node in self.nodes:
            coords = self.canvas.coords(node.rect_id)
            if coords:
                if coords[0] < min_x: min_x = coords[0]
                if coords[2] > max_x: max_x = coords[2]
                if coords[1] < min_y: min_y = coords[1]
                if coords[3] > max_y: max_y = coords[3]
        content_cx = (min_x + max_x) / 2
        content_cy = (min_y + max_y) / 2
        screen_w = self.canvas.winfo_width()
        screen_h = self.canvas.winfo_height()
        target_left = content_cx - (screen_w / 2)
        target_top = content_cy - (screen_h / 2)
        region_min, region_total = -10000, 20000
        self.canvas.xview_moveto((target_left - region_min) / region_total)
        self.canvas.yview_moveto((target_top - region_min) / region_total)

    def reset_zoom(self):
        scale_factor = 1.0 / self.zoom_level
        self.canvas.scale("all", 0, 0, scale_factor, scale_factor)
        self.zoom_level = 1.0
        self.update_ui_scaling()
        self.root.update_idletasks()
        self.center_view()

    def start_pan(self, event): self.canvas.scan_mark(event.x, event.y)
    def pan_move(self, event): self.canvas.scan_dragto(event.x, event.y, gain=1)
    def do_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        new_zoom = self.zoom_level * factor
        if 0.2 < new_zoom < 3.0:
            self.canvas.scale("all", self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), factor, factor)
            self.zoom_level = new_zoom
            self.update_ui_scaling()

    def update_ui_scaling(self):
        percentage = int(self.zoom_level * 100)
        self.lbl_zoom.config(text=f"{percentage}%")
        new_fs = int(BASE_FONT_SIZE * self.zoom_level)
        for t in self.canvas.find_withtag("text_content"): self.canvas.itemconfig(t, font=("Arial", new_fs))
        for t in self.canvas.find_withtag("text_label"): self.canvas.itemconfig(t, font=("Arial", int(new_fs*0.7), "bold"))
        for node in self.nodes:
            node.sync_coords(); node.update_text_wrapping()
            if node == self.selected_object: node.draw_handle()
        for conn in self.connections: conn.draw()

    def update_connections(self, moved_node):
        for conn in self.connections:
            if conn.parent == moved_node or conn.child == moved_node: conn.draw()

    def on_mouse_move(self, event):
        if self.connect_mode: return
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        items = self.canvas.find_overlapping(x-2, y-2, x+2, y+2)
        cursor = ""
        for item in items:
            tags = self.canvas.gettags(item)
            if "resize_grip" in tags: cursor = "sizing"; break
        self.canvas.config(cursor=cursor)

    def on_canvas_click(self, event):
        if self.connect_mode and self.connect_source:
            target = self.find_node_at(event.x, event.y)
            if target and target != self.connect_source:
                self.connections.append(Connection(self, self.connect_source, target))
            self.connect_mode = False; self.connect_source = None; self.canvas.config(cursor=""); return

        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        items = self.canvas.find_overlapping(cx-2, cy-2, cx+2, cy+2)
        for item in items:
            tags = self.canvas.gettags(item)
            if "resize_grip" in tags:
                if isinstance(self.selected_object, LogicNode):
                    self.drag_data["mode"] = "resize"; self.drag_data["x"] = event.x; self.drag_data["y"] = event.y; return
        if self.selected_object:
            self.selected_object.set_selected(False); self.selected_object = None; self.disable_all_panels()
        node = self.find_node_at(event.x, event.y)
        if node:
            self.select_object(node)
            self.drag_data["mode"] = "move"; self.drag_data["item"] = node; self.drag_data["x"] = event.x; self.drag_data["y"] = event.y; return
        items = self.canvas.find_overlapping(cx-10, cy-10, cx+10, cy+10)
        for item_id in items:
            tags = self.canvas.gettags(item_id)
            if "connection" in tags:
                for conn in self.connections:
                    if conn.line_id == item_id: self.select_object(conn); return
        self.drag_data["mode"] = "pan"
        self.canvas.scan_mark(event.x, event.y)
        
    def on_drag(self, event):
        if self.drag_data["mode"] == "move":
            node = self.drag_data["item"]
            if node:
                dx = (event.x - self.drag_data["x"]); dy = (event.y - self.drag_data["y"])
                node.move(dx, dy)
                self.drag_data["x"] = event.x; self.drag_data["y"] = event.y
        elif self.drag_data["mode"] == "resize":
            node = self.selected_object
            if node and isinstance(node, LogicNode):
                dx = (event.x - self.drag_data["x"]) / self.zoom_level
                dy = (event.y - self.drag_data["y"]) / self.zoom_level
                node.resize(node.width + dx, node.height + dy)
                self.var_w.set(int(node.width)); self.var_h.set(int(node.height))
                self.drag_data["x"] = event.x; self.drag_data["y"] = event.y
        elif self.drag_data["mode"] == "pan":
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            
    def on_drop(self, event): self.drag_data["mode"] = None; self.drag_data["item"] = None

    def populate_node_panel(self, node):
        self.var_type.set(node.node_type)
        self.txt_argument.delete("1.0", tk.END)
        self.txt_argument.insert("1.0", node.text)
        self.var_w.set(int(node.width)); self.var_h.set(int(node.height))
        self.refresh_ref_tree(node)
        self.clear_ref_details()

    def apply_manual_size(self):
        if isinstance(self.selected_object, LogicNode):
            try:
                w = self.var_w.get(); h = self.var_h.get()
                self.selected_object.resize(w, h)
            except: pass

    def select_object(self, obj):   
        self.selected_object = obj
        obj.set_selected(True)
        if isinstance(obj, LogicNode):
            self.enable_node_panel()
            self.populate_node_panel(obj)
        elif isinstance(obj, Connection):
            self.disable_all_panels()

    def find_node_at(self, sx, sy):
        cx, cy = self.canvas.canvasx(sx), self.canvas.canvasy(sy)
        for node in self.nodes:
            coords = self.canvas.coords(node.rect_id)
            if coords and coords[0] <= cx <= coords[2] and coords[1] <= cy <= coords[3]: return node
        return None

    def context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        node = self.find_node_at(event.x, event.y)
        if node:
            menu.add_command(label="Connect Arrow", command=lambda: self.start_connect(node))
            menu.add_command(label="Delete Node", command=lambda: self.delete_object(node))
        else:
            menu.add_command(label="Add Question", command=lambda: self.add_node("Question", event.x, event.y))
            menu.add_command(label="Add Problem", command=lambda: self.add_node("Problem", event.x, event.y))
            menu.add_command(label="Add Solution", command=lambda: self.add_node("Solution", event.x, event.y))
            menu.add_command(label="Add Explanation", command=lambda: self.add_node("Explanation", event.x, event.y))
            # --- NEW LINE HERE ---
            menu.add_command(label="Add Conclusion", command=lambda: self.add_node("Conclusion", event.x, event.y))
        menu.post(event.x_root, event.y_root)

    def start_connect(self, node):
        self.connect_mode = True; self.connect_source = node; self.canvas.config(cursor="crosshair")

    def refresh_ref_tree(self, node):
        for item in self.ref_tree.get_children():
            self.ref_tree.delete(item)
        for ref in node.references:
            display_title = ref.get('title', '') or "(No Title)"
            pdf = ref.get('file', '')
            self.ref_tree.insert("", tk.END, iid=ref['id'], values=(display_title, ref['link'], pdf))

    def on_ref_select(self, event):
        selected_id = self.ref_tree.selection()
        if not selected_id: return
        ref_id = selected_id[0]
        if isinstance(self.selected_object, LogicNode):
            ref_data = next((r for r in self.selected_object.references if r['id'] == ref_id), None)
            if ref_data:
                self.ent_ref_title.delete(0, tk.END); self.ent_ref_title.insert(0, ref_data.get('title', ''))
                self.ent_ref_link.delete(0, tk.END); self.ent_ref_link.insert(0, ref_data.get('link', ''))
                self.ent_ref_file.configure(state='normal'); self.ent_ref_file.delete(0, tk.END)
                self.ent_ref_file.insert(0, ref_data.get('file', '')); self.ent_ref_file.configure(state='readonly')
                self.txt_ref_desc.delete("1.0", tk.END); self.txt_ref_desc.insert("1.0", ref_data.get('desc', ''))

    def save_node_details(self, event=None):
        if isinstance(self.selected_object, LogicNode):
            self.selected_object.node_type = self.var_type.get()
            self.selected_object.text = self.txt_argument.get("1.0", tk.END).strip()
            self.selected_object.update_visuals()
            return "break"

    def save_reference(self, event=None):
        if not isinstance(self.selected_object, LogicNode): return
        link = self.ent_ref_link.get().strip()
        title = self.ent_ref_title.get().strip()
        desc = self.txt_ref_desc.get("1.0", tk.END).strip()
        file_path = self.ent_ref_file.get().strip()

        sel_id = self.ref_tree.selection()
        if sel_id:
            ref_id = sel_id[0]
            for ref in self.selected_object.references:
                if ref['id'] == ref_id:
                    ref['title'] = title; ref['link'] = link; ref['desc'] = desc; ref['file'] = file_path
        else:
            new_ref = {'id': str(uuid.uuid4()), 'title': title, 'link': link, 'desc': desc, 'file': file_path}
            self.selected_object.references.append(new_ref)
        
        self.refresh_ref_tree(self.selected_object)
        self.clear_ref_details()
        return "break"

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
        self.ent_ref_file.configure(state='normal'); self.ent_ref_file.delete(0, tk.END); self.ent_ref_file.configure(state='readonly')
        self.txt_ref_desc.delete("1.0", tk.END)
        if self.ref_tree.selection():
            self.ref_tree.selection_remove(self.ref_tree.selection())

    def disable_all_panels(self):
        for child in self.right_panel.winfo_children():
            for sub in child.winfo_children():
                try: sub.configure(state='disabled') 
                except: pass

    def enable_node_panel(self):
        for child in self.right_panel.winfo_children():
            for sub in child.winfo_children():
                try: sub.configure(state='normal')
                except: pass
        self.cb_type.configure(state="readonly")
        self.ent_ref_file.configure(state='readonly') 

    def delete_selected_object(self):
        if self.selected_object:
            self.delete_object(self.selected_object)
            self.selected_object = None; self.disable_all_panels()

    def delete_object(self, obj):
        if isinstance(obj, Connection):
            obj.delete()
            if obj in self.connections: self.connections.remove(obj)
        elif isinstance(obj, LogicNode):
            self.canvas.delete(obj.rect_id); self.canvas.delete(obj.text_id); self.canvas.delete(obj.type_id)
            obj.set_selected(False) 
            to_remove = [c for c in self.connections if c.parent == obj or c.child == obj]
            for c in to_remove:
                c.delete(); self.connections.remove(c)
            if obj in self.nodes: self.nodes.remove(obj)

    def add_node(self, n_type, x, y):
        cx, cy = self.canvas.canvasx(x), self.canvas.canvasy(y)
        node = LogicNode(self, cx, cy, n_type)
        self.nodes.append(node)

    def save_to_xml(self):
        path = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML", "*.xml")])
        if not path: return
        root = ET.Element("ThesisFlow", project_id=self.project_id)
        for n in self.nodes:
            ne = ET.SubElement(root, "Node", id=n.id, type=n.node_type, x=str(n.x), y=str(n.y), w=str(n.width), h=str(n.height))
            ET.SubElement(ne, "Text").text = n.text
            re = ET.SubElement(ne, "References")
            for ref in n.references:
                r_item = ET.SubElement(re, "Ref", id=ref['id'])
                ET.SubElement(r_item, "Title").text = ref.get('title', '')
                ET.SubElement(r_item, "Link").text = ref.get('link', '')
                ET.SubElement(r_item, "File").text = ref.get('file', '')
                ET.SubElement(r_item, "Desc").text = ref.get('desc', '')
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
            # --- PERUBAHAN 5: Load Project ID atau buat baru jika tidak ada ---
            self.project_id = root.get('project_id', str(uuid.uuid4()))
            # ----------------------------------------------------------------
            for n in list(self.nodes): self.delete_object(n)
            id_map = {}
            for ne in root.findall("Node"):
                w = float(ne.get('w')) if ne.get('w') else BASE_NODE_WIDTH
                h = float(ne.get('h')) if ne.get('h') else BASE_NODE_HEIGHT
                node = LogicNode(self, float(ne.get('x')), float(ne.get('y')), ne.get('type'), 
                                 text=ne.find("Text").text or "", node_id=ne.get('id'), width=w, height=h)
                ref_container = ne.find("References")
                if ref_container is not None:
                    for r_xml in ref_container.findall("Ref"):
                        f_node = r_xml.find("File")
                        f_text = f_node.text if (f_node is not None) else ""
                        node.references.append({
                            'id': r_xml.get('id', str(uuid.uuid4())),
                            'title': r_xml.find("Title").text or "",
                            'link': r_xml.find("Link").text or "",
                            'file': f_text,
                            'desc': r_xml.find("Desc").text or ""
                        })
                node.update_visuals()
                self.nodes.append(node)
                id_map[node.id] = node
            conn_root = root.find("Connections")
            if conn_root is not None:
                for link in conn_root.findall("Link"):
                    pid, cid = link.get("parent"), link.get("child")
                    if pid in id_map and cid in id_map:
                        self.connections.append(Connection(self, id_map[pid], id_map[cid]))
            self.center_view()
        except Exception as e: messagebox.showerror("Error", str(e))

    def show_global_references(self):
        lines = ["--- BIBLIOGRAPHY EXPORT ---", ""]
        for n in self.nodes:
            if n.references:
                lines.append(f"[{n.node_type}] {n.text}")
                for r in n.references:
                    file_info = f" [PDF: {r.get('file')}]" if r.get('file') else ""
                    lines.append(f"   • {r['title']} ({r['link']}){file_info}")
                    if r['desc']:
                        desc_lines = r['desc'].split('\n')
                        for i, line in enumerate(desc_lines):
                            prefix = "     Note: " if i == 0 else "           "
                            lines.append(f"{prefix}{line}")
                lines.append("")
        top = tk.Toplevel(self.root)
        top.geometry("600x500")
        t = tk.Text(top, padx=10, pady=10)
        t.pack(fill=tk.BOTH, expand=True)
        t.insert("1.0", "\n".join(lines))

    def show_about(self):
        messagebox.showinfo("About", f"{constants.TITLE} {constants.VERSION[0]}.{constants.VERSION[1]}.{constants.VERSION[2]}\n\n{constants.DESCRIPTION}")