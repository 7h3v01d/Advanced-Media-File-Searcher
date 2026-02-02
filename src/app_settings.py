import os
import json

class AppSettings:
    """
    Manages application settings, including loading defaults, loading from/saving to a file.
    """
    _SETTINGS_FILE = "settings.json"
    _DEFAULT_SETTINGS = {
        "max_scan_depth": 5,  # Default scan depth
        "excluded_file_types": [".tmp", ".log", ".DS_Store", ".ini", ".db"], # Default excluded types
        # Add other default settings here as they are introduced
        "default_search_location": os.path.expanduser("~") if os.name == 'posix' else os.getcwd(),
        "default_batch_input_folder": os.path.expanduser("~") if os.name == 'posix' else os.getcwd(),
        "default_batch_output_folder": os.path.expanduser("~") if os.name == 'posix' else os.getcwd(),
        "default_search_type": "TV Show",
        "default_exact_match": False,
        "default_batch_instance_mode": "Multiple",
        "default_dark_mode": False,
        "default_debug_mode": False,
        "default_exclude_filetypes": ".tmp, .log, .nfo, .txt", # Added this default setting
        # Future additions:
        "output_font_size": 10,
        "output_font_family": "TkDefaultFont",
    }

    def __init__(self):
        self.settings = self._DEFAULT_SETTINGS.copy()
        self._load_settings()

    def _load_settings(self):
        """Loads settings from the settings file, or uses defaults if file not found/corrupt."""
        if os.path.exists(self._SETTINGS_FILE):
            try:
                with open(self._SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # Merge loaded settings with defaults to handle new settings gracefully
                    self.settings = {**self._DEFAULT_SETTINGS, **loaded_settings}
                print(f"INFO: Settings loaded from {self._SETTINGS_FILE}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"WARNING: Could not load settings from {self._SETTINGS_FILE}: {e}. Using default settings.")
                self.settings = self._DEFAULT_SETTINGS.copy()
        else:
            print(f"INFO: Settings file {self._SETTINGS_FILE} not found. Using default settings.")

    def save_settings(self):
        """Saves the current settings to the settings file."""
        try:
            with open(self._SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            print(f"INFO: Settings saved to {self._SETTINGS_FILE}")
        except IOError as e:
            print(f"ERROR: Could not save settings to {self._SETTINGS_FILE}: {e}")

    def get_setting(self, key):
        """Retrieves a specific setting value."""
        return self.settings.get(key)

    def set_setting(self, key, value):
        """Sets a specific setting value."""
        if key in self.settings: # Only allow setting existing keys for now
            self.settings[key] = value
            self.save_settings() # Save immediately after setting a value
        else:
            print(f"WARNING: Attempted to set unknown setting key: {key}")

    def reset_to_defaults(self):
        """Resets all settings to their default values and saves them."""
        self.settings = self._DEFAULT_SETTINGS.copy()
        self.save_settings()
        print("INFO: Settings reset to defaults.")

# Example Usage (for testing purposes, remove in final integration)
if __name__ == "__main__":
    settings_manager = AppSettings()

    print("\nInitial Settings:")
    print(f"Max Scan Depth: {settings_manager.get_setting('max_scan_depth')}")
    print(f"Excluded File Types: {settings_manager.get_setting('excluded_file_types')}")
    print(f"Default Dark Mode: {settings_manager.get_setting('default_dark_mode')}")

    # Change a setting
    settings_manager.set_setting("max_scan_depth", 10)
    settings_manager.set_setting("excluded_file_types", [".bak", ".temp"])
    settings_manager.set_setting("new_unregistered_setting", "should_not_be_set") # This will trigger warning

    print("\nSettings after modification and save:")
    print(f"Max Scan Depth: {settings_manager.get_setting('max_scan_depth')}")
    print(f"Excluded File Types: {settings_manager.get_setting('excluded_file_types')}")

    # Load again to confirm persistence
    new_settings_manager = AppSettings()
    print("\nSettings after re-loading app (should be persistent):")
    print(f"Max Scan Depth: {new_settings_manager.get_setting('max_scan_depth')}")
    print(f"Excluded File Types: {new_settings_manager.get_setting('excluded_file_types')}")

    # Reset to defaults
    new_settings_manager.reset_to_defaults()
    print("\nSettings after reset to defaults:")
    print(f"Max Scan Depth: {new_settings_manager.get_setting('max_scan_depth')}")
    print(f"Excluded File Types: {new_settings_manager.get_setting('excluded_file_types')}")

