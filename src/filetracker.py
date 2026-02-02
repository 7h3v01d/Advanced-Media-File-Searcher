import os
import re
import threading
import time

# Assuming AppSettings is in the same directory or accessible via PYTHONPATH
from app_settings import AppSettings # Import the AppSettings class

class FileTracker:
    """
    Tracks files within a specified directory, providing search functionality
    with filtering and debug output. It's responsible for the recursive scanning
    of the file system.
    """
    def __init__(self, app_settings_instance):
        """
        Initializes the FileTracker.

        Args:
            app_settings_instance (AppSettings): An instance of the AppSettings manager
                                                 to retrieve configuration like scan depth
                                                 and excluded file types.
        """
        self.files_data = []  # Stores list of dictionaries for found files
        self.stop_event = threading.Event() # Event to signal stopping the search
        self.app_settings = app_settings_instance # Store the AppSettings instance

    def set_stop_event(self, stop_event):
        """Sets the stop event from an external source (e.g., FileSearchService)."""
        self.stop_event = stop_event

    def scan_files(self, search_location, update_callback=None, current_depth=0):
        """
        Recursively scans the specified directory for files.
        Collects file information (name, path, size) and calls an update callback.

        Args:
            search_location (str): The root directory to start scanning from.
            update_callback (callable, optional): A callback function to report progress.
                                                  Defaults to None.
            current_depth (int): The current recursion depth. Used with max_scan_depth.
        """
        if self.stop_event.is_set():
            return # Stop scanning if the stop event is set

        max_depth = self.app_settings.get_setting("max_scan_depth")
        # Check against max_depth (0 means no limit)
        if max_depth != 0 and current_depth >= max_depth:
            # print(f"DEBUG: Max scan depth ({max_depth}) reached for {search_location}. Skipping.")
            return

        try:
            for entry in os.scandir(search_location):
                if self.stop_event.is_set():
                    return # Stop if requested during iteration

                if entry.is_file():
                    if not self._is_excluded(entry.name):
                        try:
                            file_size = entry.stat().st_size
                            file_info = {
                                'name': entry.name,
                                'raw_path': entry.path,
                                'size_bytes': file_size
                            }
                            self.files_data.append(file_info)
                            if update_callback:
                                update_callback(f"Found file: {entry.name}")
                        except OSError as e:
                            print(f"WARNING: Could not access file {entry.path}: {e}")
                elif entry.is_dir():
                    # Recursively call scan_files for subdirectories
                    self.scan_files(entry.path, update_callback, current_depth + 1)
        except PermissionError:
            print(f"WARNING: Permission denied when accessing: {search_location}. Skipping.")
        except FileNotFoundError:
            print(f"ERROR: Directory not found: {search_location}. Please check the path.")
        except Exception as e:
            print(f"ERROR: An unexpected error occurred in {search_location}: {e}")

    def search_files(self, search_term, search_location, selected_type, exact_match_mode, update_callback=None):
        """
        Performs the file search operation.

        Args:
            search_term (str): The term to search for.
            search_location (str): The directory to search in.
            selected_type (str): The content type filter ("Movie", "TV Show", "Other", "All").
            exact_match_mode (bool): If True, performs an exact match search.
            update_callback (callable, optional): A callback for progress updates.
        """
        self.files_data = [] # Clear previous results
        self.stop_event.clear() # Clear stop event for a new search

        print(f"INFO: FileTracker: Starting scan in '{search_location}' for term '{search_term}' (Exact Match: {exact_match_mode}).")
        
        # Start the recursive scan
        self.scan_files(search_location, update_callback)

        if self.stop_event.is_set():
            print("INFO: FileTracker: File scanning interrupted by user.")
            return []

        # At this point, self.files_data contains all *scanned* files,
        # irrespective of the search term or filters. The filtering logic
        # is now primarily handled by the FileSearchService after classification.
        # This method's main job is just to gather the raw file data.
        print(f"INFO: FileTracker: Finished scanning. Total files found by scanner: {len(self.files_data)}")
        return self.files_data # Return all scanned files for further processing

    def _is_excluded(self, filename):
        """
        Checks if a file should be excluded based on its extension.
        Reads excluded types from AppSettings.
        """
        excluded_types = self.app_settings.get_setting("excluded_file_types")
        if not excluded_types:
            return False # No types to exclude

        file_extension = os.path.splitext(filename)[1].lower()
        return file_extension in [ext.lower() for ext in excluded_types]

    def _exact_match(self, filename, search_term):
        """
        Performs an exact match comparison, considering both full filename and base filename.
        """
        # Exact match with extension
        if filename.lower() == search_term.lower():
            return True
        
        # Exact match without extension
        base_name, _ = os.path.splitext(filename)
        if base_name.lower() == search_term.lower():
            return True
            
        return False

    def _smart_match(self, filename, search_term):
        """
        Performs a 'smart' (partial/fuzzy) match using regex.
        This part remains flexible for more sophisticated matching.
        """
        # Escape special characters in search_term for regex
        search_term_escaped = re.escape(search_term)
        
        # Make the regex case-insensitive and allow partial matches
        # This regex looks for the search term anywhere in the filename
        # You can make this more sophisticated if needed (e.g., word boundaries)
        match_pattern = r".*" + search_term_escaped + r".*"
        
        if re.search(match_pattern, filename, re.IGNORECASE):
            return True
        return False

