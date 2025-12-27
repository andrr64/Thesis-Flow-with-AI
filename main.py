# main.py
import tkinter as tk
from ui.app_window import ThesisFlowApp


if __name__ == "__main__":
    # Create Root Window
    root = tk.Tk()
    
    # Initialize Application
    app = ThesisFlowApp(root)
    
    # Run
    root.mainloop()