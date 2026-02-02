import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

# Import AppSettings for persistent storage
from app_settings import AppSettings
# Import TextRedirector and other utilities if needed for logging
from gui_utilities import TextRedirector

class SettingsTabFrame(tk.Frame):
    def __init__(self, parent_notebook, master_app_instance, app_settings_instance, text_redirector, debug_info_var, dark_mode_var):
        """
        Initializes the SettingsTabFrame.

        Args:
            parent_notebook (ttk.Notebook): The notebook widget this tab will be added to.
            master_app_instance (FileSearchGUI): Reference to the main GUI application instance.
            app_settings_instance (AppSettings): Reference to the AppSettings instance for persistent settings.
            text_redirector (TextRedirector): The custom stdout redirector for GUI logging.
            debug_info_var (tk.BooleanVar): A BooleanVar controlling debug output visibility.
            dark_mode_var (tk.BooleanVar): A BooleanVar controlling dark mode state.
        """
        super().__init__(parent_notebook)
        self.master_app = master_app_instance # Store reference to main app
        self.app_settings = app_settings_instance # Store AppSettings instance
        self.text_redirector = text_redirector
        self.debug_info_var = debug_info_var
        self.dark_mode_var = dark_mode_var

        # Configure grid for this frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        for i in range(10): # Enough rows for widgets before the output
            self.grid_rowconfigure(i, weight=0)
        # Row for the output text area should expand
        self.grid_rowconfigure(8, weight=1) 


        # Dark Mode Checkbox (moved from main GUI to settings tab)
        self.dark_mode_checkbox = tk.Checkbutton(self, text="Dark Mode (Default)", variable=self.dark_mode_var,
                                  command=self._toggle_dark_mode_from_settings)
        self.dark_mode_checkbox.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        # Show Debug Info Checkbox
        self.debug_info_checkbox = tk.Checkbutton(self, text="Show Debug Info (Default)", variable=self.debug_info_var,
                                                  command=self._toggle_debug_info_from_settings)
        self.debug_info_checkbox.grid(row=1, column=0, sticky="w", padx=10, pady=(5, 10))


        # Default Search Folder
        self.default_search_location_label = tk.Label(self, text="Default Search Folder:")
        self.default_search_location_label.grid(row=2, column=0, sticky="w", padx=10, pady=(10, 0))

        self.default_search_location_entry = tk.Entry(self, width=60)
        self.default_search_location_entry.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))

        self.browse_default_folder_button = tk.Button(self, text="Browse Folder", command=self._browse_default_folder,
                                                       relief="raised", bd=2, padx=10, pady=5)
        self.browse_default_folder_button.grid(row=3, column=1, sticky="ew", padx=10, pady=(0, 5))


        # Default Exclude File Types
        self.default_exclude_filetypes_label = tk.Label(self, text="Default Exclude File Types (comma-separated):")
        self.default_exclude_filetypes_label.grid(row=4, column=0, sticky="w", padx=10, pady=(10, 0))

        self.default_exclude_filetypes_entry = tk.Entry(self, width=60)
        self.default_exclude_filetypes_entry.grid(row=5, column=0, sticky="ew", padx=10, pady=(0, 5))

        # Save Settings Button
        self.save_settings_button = tk.Button(self, text="Save Settings", command=self._save_settings_to_app_settings,
                                               relief="raised", bd=2, padx=20, pady=10, font=("TkDefaultFont", 10, "bold"))
        self.save_settings_button.grid(row=6, column=0, columnspan=2, pady=20)


        # Settings Output Area
        self.output_label = tk.Label(self, text="Settings Output:")
        self.output_label.grid(row=7, column=0, sticky="w", padx=10, pady=(10, 0))

        # Clear Output Button for settings tab
        self.clear_settings_output_button = tk.Button(self, text="Clear Output", command=self.clear_settings_output,
                                            relief="raised", bd=2, padx=5, pady=2, font=("TkDefaultFont", 9))
        self.clear_settings_output_button.grid(row=7, column=1, sticky="e", padx=10, pady=(10,0))


        self.output_text = tk.Text(self, wrap="word", height=10, width=120, relief="sunken", bd=1)
        self.output_text.grid(row=8, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))

        self.output_scrollbar = tk.Scrollbar(self, command=self.output_text.yview)
        self.output_scrollbar.grid(row=8, column=2, sticky="ns", pady=(0, 10))
        self.output_text['yscrollcommand'] = self.output_scrollbar.set

        # Set the output text widget for the redirector
        # This will be overridden by gui_app.py when switching tabs
        # but is useful for initial setup and direct prints from this tab
        self.text_redirector.set_output_text_widget(self.output_text)

        # Load initial settings into GUI
        self._load_current_settings_to_gui()


    def apply_theme(self, theme, ttk_style):
        """Applies the current theme colors to all widgets within this tab."""
        self.config(bg=theme["bg"])

        # Labels
        for label in [self.default_search_location_label, self.default_exclude_filetypes_label, self.output_label]:
            if label and label.winfo_exists():
                label.config(bg=theme["bg"], fg=theme["label_fg"])

        # Checkboxes
        if self.dark_mode_checkbox and self.dark_mode_checkbox.winfo_exists():
            self.dark_mode_checkbox.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])
        if self.debug_info_checkbox and self.debug_info_checkbox.winfo_exists():
            self.debug_info_checkbox.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])

        # Entries
        if self.default_search_location_entry and self.default_search_location_entry.winfo_exists():
            self.default_search_location_entry.config(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"], state=tk.NORMAL)
        if self.default_exclude_filetypes_entry and self.default_exclude_filetypes_entry.winfo_exists():
            self.default_exclude_filetypes_entry.config(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"], state=tk.NORMAL)

        # Buttons
        if self.browse_default_folder_button and self.browse_default_folder_button.winfo_exists():
            self.browse_default_folder_button.config(bg=theme["button_bg"], fg=theme["button_fg"], activebackground=theme["button_bg"])
        if self.save_settings_button and self.save_settings_button.winfo_exists():
            self.save_settings_button.config(bg=theme["start_button_bg"], fg=theme["button_fg"], activebackground=theme["start_button_bg"])
        if self.clear_settings_output_button and self.clear_settings_output_button.winfo_exists():
            self.clear_settings_output_button.config(bg=theme["clear_button_bg"], fg=theme["button_fg"], activebackground=theme["clear_button_bg"])

        # Output Text Area (general background/foreground)
        if self.output_text and self.output_text.winfo_exists():
            self.output_text.config(bg=theme["output_bg"], fg=theme["output_fg"])
            
            # Apply colors to specific output text tags
            self.output_text.tag_config("error", foreground=theme["error_fg"])
            self.output_text.tag_config("info", foreground=theme["info_fg"])
            self.output_text.tag_config("debug", foreground=theme["debug_fg"])
            self.output_text.tag_config("warning", foreground=theme["warning_fg"])
            self.output_text.tag_config("summary_not_found", foreground=theme["summary_not_found_fg"])
            self.output_text.tag_config("summary_found", foreground=theme["summary_found_fg"])
            self.output_text.tag_config("category_header", foreground=theme["category_header_fg"])
            self.output_text.tag_config("item_detail", foreground=theme["item_detail_fg"])
            self.output_text.tag_config("item_detail_parsed", foreground=theme["item_detail_parsed_fg"])
            self.output_text.tag_config("summary_header_bold_large", font=("TkDefaultFont", 12, "bold"), foreground=theme["category_header_fg"])


    def _toggle_dark_mode_from_settings(self):
        """
        Calls the main application's method to toggle dark mode.
        This internal method acts as a wrapper for the command binding.
        """
        self.master_app.toggle_dark_mode()
        # No need to save here, as toggle_dark_mode in gui_app.py already saves to app_settings

    def _toggle_debug_info_from_settings(self):
        """
        Toggles the debug info state and updates the TextRedirector.
        """
        is_debug = self.debug_info_var.get()
        self.text_redirector.set_debug_mode(is_debug)
        self.app_settings.set_setting("default_debug_mode", is_debug)
        print(f"INFO: Settings: Debug info toggled to: {is_debug}")

    def _load_current_settings_to_gui(self):
        """Loads current settings from AppSettings into the GUI widgets."""
        self.dark_mode_var.set(self.app_settings.get_setting("default_dark_mode"))
        self.debug_info_var.set(self.app_settings.get_setting("default_debug_mode"))

        # Corrected: Call get_setting with only the key, then provide fallback
        default_search_folder = self.app_settings.get_setting("default_search_location")
        if not default_search_folder: # If setting is not found or empty
            default_search_folder = os.path.expanduser("~")
        self.default_search_location_entry.delete(0, tk.END)
        self.default_search_location_entry.insert(0, default_search_folder)

        # Corrected: Call get_setting with only the key, then provide fallback
        default_exclude_filetypes = self.app_settings.get_setting("default_exclude_filetypes")
        if not default_exclude_filetypes: # If setting is not found or empty
            default_exclude_filetypes = ".tmp, .log, .nfo, .txt"
        self.default_exclude_filetypes_entry.delete(0, tk.END)
        self.default_exclude_filetypes_entry.insert(0, default_exclude_filetypes)
        print("INFO: Settings loaded into GUI.")

    def _save_settings_to_app_settings(self):
        """Saves current GUI settings to AppSettings."""
        self.app_settings.set_setting("default_search_location", self.default_search_location_entry.get().strip())
        self.app_settings.set_setting("default_exclude_filetypes", self.default_exclude_filetypes_entry.get().strip())
        # Dark mode and debug info are saved automatically by their respective toggle commands

        self.app_settings.save_settings() # Explicitly save to file
        messagebox.showinfo("Settings", "Settings saved successfully!")
        print("INFO: Settings saved from GUI.")
    
    def _browse_default_folder(self):
        """Opens a directory dialog for selecting the default search location."""
        folder_path = filedialog.askdirectory(
            parent=self.master_app.master,
            initialdir=self.default_search_location_entry.get() if self.default_search_location_entry.get() else os.path.expanduser("~"),
            title="Select Default Search Folder"
        )
        if folder_path:
            self.default_search_location_entry.delete(0, tk.END)
            self.default_search_location_entry.insert(0, folder_path)
            print(f"INFO: Settings: Default search folder selected: {folder_path}")
        else:
            print("INFO: Settings: Default search folder selection cancelled.")

    def clear_settings_output(self):
        """Clears the settings output text area."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        print("INFO: Settings output area cleared.")
