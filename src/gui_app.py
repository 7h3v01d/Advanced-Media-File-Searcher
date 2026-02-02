import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sys
import os
import re
import threading
import time
import subprocess 

# Import modularized components
from base_parser import BaseParser
from search_service import FileSearchService
from gui_utilities import TextRedirector, format_bytes 
from search_tab import SearchTabFrame
from batch_tab import BatchTabFrame
from settings_tab import SettingsTabFrame
from themes import light_theme, dark_theme # Import themes


# --- Main GUI Application Class ---
class FileSearchGUI:
    def __init__(self, master):
        self.master = master
        master.title("Advanced Media File Searcher")
        master.geometry("1000x800")
        master.resizable(True, True)

        # --- Color Themes ---
        # Themes are now imported from themes.py
        self.light_theme = light_theme
        self.dark_theme = dark_theme
        self.current_theme = self.light_theme # Default theme

        # Master window grid now primarily holds the notebook
        master.grid_columnconfigure(0, weight=1) 
        master.grid_rowconfigure(0, weight=1)

        # Initialize ttk Style
        self.style = ttk.Style()

        # Initialize core services
        self.search_service = FileSearchService()

        # Dark Mode checkbox state for the main app (moved from old location)
        self.dark_mode_var = tk.BooleanVar()
        self.dark_mode_var.set(False) # Default to light mode

        # Debug Info checkbox state for the main app (moved from old location)
        self.debug_info_var = tk.BooleanVar()
        self.debug_info_var.set(False) # Default to debug info OFF

        # Initialize TextRedirector with the debug_info_var
        self.original_stdout = sys.stdout
        self.text_redirector = TextRedirector(debug_var=self.debug_info_var, buffer_limit=100) 
        sys.stdout = self.text_redirector
        
        # --- Widgets ---
        # Notebook (Tabbed Interface)
        self.notebook = ttk.Notebook(master)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10) # Place notebook in main window

        # Initialize tab frames
        self.search_tab = SearchTabFrame(self.notebook, self, self.search_service, self.text_redirector, self.debug_info_var, self.dark_mode_var)
        # Pass necessary arguments to BatchTabFrame
        self.batch_tab = BatchTabFrame(self.notebook, self, self.search_service, self.text_redirector, self.debug_info_var, self.dark_mode_var)
        self.settings_tab = SettingsTabFrame(self.notebook, self) # Pass self for dark mode toggling

        # Add tabs to the notebook
        self.notebook.add(self.search_tab, text="Search")
        self.notebook.add(self.batch_tab, text="Batch")
        self.notebook.add(self.settings_tab, text="Settings")

        # Apply initial theme
        self.apply_theme()
        
        print("INFO: GUI ready. Enter search term and select folder to start search.")
        
        # Overlay properties
        self.overlay_window = None
        self.progress_bar = None

    def apply_theme(self):
        """Applies the current theme colors to all widgets."""
        theme = self.current_theme
        self.master.config(bg=theme["bg"])

        # Configure Notebook tab appearance
        notebook_style_name = "Custom.TNotebook"
        self.style.configure(notebook_style_name,
                             background=theme["notebook_bg"],
                             fieldbackground=theme["notebook_bg"],
                             bordercolor=theme["notebook_bg"],
                             lightcolor=theme["notebook_bg"],
                             darkcolor=theme["notebook_bg"],
                             relief="flat",
                             padding=0,
                             tabmargins=[0, 0, 0, 0])
        self.style.configure(f"{notebook_style_name}.Tab",
                             background=theme["notebook_bg"],
                             foreground=theme["notebook_fg"],
                             bordercolor=theme["notebook_bg"],
                             lightcolor=theme["notebook_bg"],
                             darkcolor=theme["notebook_bg"],
                             padding=[10, 5],
                             relief="flat",
                             focuscolor=theme["notebook_bg"])
        self.style.map(f"{notebook_style_name}.Tab",
                       background=[("selected", theme["notebook_selected_bg"]), ("!selected", theme["notebook_bg"])],
                       foreground=[("selected", theme["notebook_selected_fg"]), ("!selected", theme["notebook_fg"])],
                       bordercolor=[("selected", theme["notebook_selected_bg"]), ("!selected", theme["notebook_bg"])],
                       lightcolor=[("selected", theme["notebook_selected_bg"]), ("!selected", theme["notebook_bg"])],
                       darkcolor=[("selected", theme["notebook_selected_bg"]), ("!selected", theme["notebook_bg"])])
        self.notebook.configure(style=notebook_style_name)

        # Configure the TProgressbar style for the indeterminate mode
        self.style.configure("Custom.Horizontal.TProgressbar",
                             background=theme["button_bg"], # Color of the moving bar
                             troughcolor=theme["entry_bg"], # Background of the bar
                             bordercolor=theme["button_bg"], # Border color
                             lightcolor=theme["button_bg"],
                             darkcolor=theme["button_bg"])
        self.style.map("Custom.Horizontal.TProgressbar",
                       background=[('active', theme["button_bg"]), ('!disabled', theme["button_bg"])],
                       troughcolor=[('active', theme["entry_bg"]), ('!disabled', theme["entry_bg"])],
                       bordercolor=[('active', theme["button_bg"]), ('!disabled', theme["button_bg"])])

        # Apply theme to individual tabs
        self.search_tab.apply_theme(theme, self.style)
        self.batch_tab.apply_theme(theme, self.style)
        self.settings_tab.apply_theme(theme, self.style)

    def toggle_dark_mode(self):
        """
        Toggles between light and dark themes. This method is called by the checkboxes in
        both the search and settings tabs.
        """
        if self.dark_mode_var.get():
            self.current_theme = self.dark_theme
            print("INFO: Switched to Dark Mode.")
        else:
            self.current_theme = self.light_theme
            print("INFO: Switched to Light Mode.")
        self.apply_theme() # Apply the newly set theme to all components

    def show_overlay(self):
        """Displays a 'Processing, Please Wait...' overlay with a spinner."""
        self.overlay_window = tk.Toplevel(self.master)
        self.overlay_window.title("Processing")
        self.overlay_window.transient(self.master) # Make it appear on top of the main window
        self.overlay_window.grab_set() # Disable interaction with main window

        # Center the overlay window
        self.master.update_idletasks() # Ensure main window dimensions are updated
        main_x = self.master.winfo_x()
        main_y = self.master.winfo_y()
        main_width = self.master.winfo_width()
        main_height = self.master.winfo_height()

        overlay_width = 300
        overlay_height = 100
        overlay_x = main_x + (main_width // 2) - (overlay_width // 2)
        overlay_y = main_y + (main_height // 2) - (overlay_height // 2)
        self.overlay_window.geometry(f"{overlay_width}x{overlay_height}+{overlay_x}+{overlay_y}")

        # Use ttk.Frame for styling consistency
        frame = ttk.Frame(self.overlay_window, relief="raised", borderwidth=2)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Use ttk.Label for styling consistency
        ttk.Label(frame, text="Processing, Please Wait...", font=("TkDefaultFont", 12, "bold")).pack(pady=10)
        
        # Use ttk.Progressbar for professional animation
        self.progress_bar = ttk.Progressbar(frame, mode='indeterminate', length=200, style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(pady=5)
        self.progress_bar.start(10) # Start the indeterminate animation, updating every 10ms

    def hide_overlay(self):
        """Hides and destroys the 'Processing, Please Wait!' overlay."""
        if self.overlay_window:
            if self.progress_bar: # Check if progress bar exists before stopping
                self.progress_bar.stop() # Stop the indeterminate animation
            self.overlay_window.grab_release() # Re-enable interaction with main window
            self.overlay_window.destroy()
            self.overlay_window = None
            self.progress_bar = None

    def on_closing(self):
        """Called when the window is closed, restores original stdout."""
        # Attempt to stop any running search gracefully before closing
        self.search_service.stop_search()
        # Give a small moment for the thread to recognize the stop, if needed
        time.sleep(0.1) 
        sys.stdout = self.original_stdout
        self.master.destroy()

# --- Main execution block ---
if __name__ == "__main__":
    root = tk.Tk()
    app = FileSearchGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing) # Handle window close event
    root.mainloop()

