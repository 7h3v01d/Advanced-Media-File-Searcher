import tkinter as tk
from tkinter import ttk

class SettingsTabFrame(tk.Frame):
    def __init__(self, parent_notebook, master_app_instance):
        """
        Initializes the SettingsTabFrame.

        Args:
            parent_notebook (ttk.Notebook): The notebook widget this tab will be added to.
            master_app_instance (FileSearchGUI): Reference to the main GUI application instance.
        """
        super().__init__(parent_notebook)
        self.master_app = master_app_instance # Store reference to main app

        # Placeholder content for the Settings tab
        self.settings_label = tk.Label(self, text="Application settings will go here.", font=("TkDefaultFont", 12))
        self.settings_label.pack(pady=50)

        # Dark Mode Checkbox (moved from main GUI to settings tab)
        # This checkbox directly uses the master_app's dark_mode_var
        self.dark_mode_checkbox = tk.Checkbutton(self, text="Dark Mode", variable=self.master_app.dark_mode_var,
                                  command=self._toggle_dark_mode_from_settings) # Use internal method
        self.dark_mode_checkbox.pack(pady=10)


    def apply_theme(self, theme, ttk_style):
        """Applies the current theme colors to all widgets within this tab."""
        self.config(bg=theme["bg"])
        self.settings_label.config(bg=theme["bg"], fg=theme["label_fg"])
        self.dark_mode_checkbox.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])

    def _toggle_dark_mode_from_settings(self):
        """
        Calls the main application's method to toggle dark mode.
        This internal method acts as a wrapper for the command on the checkbox.
        """
        # Corrected: Call the actual toggle_dark_mode method on the master_app
        self.master_app.toggle_dark_mode()

