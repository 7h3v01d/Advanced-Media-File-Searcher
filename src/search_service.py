import threading
import time # Import time for sleep in stop_search
import re
import os

from media_classifier import MediaClassifier # Import MediaClassifier


class FileSearchService:
    """
    Acts as a service layer to orchestrate file search operations.
    It uses FileTracker to scan files and MediaClassifier to classify them.
    Handles threading for searches to keep the GUI responsive.
    """

    def __init__(self, file_tracker_instance, base_parser_instance, debug_info_var):
        """
        Initializes the FileSearchService.

        Args:
            file_tracker_instance (FileTracker): An instance of the FileTracker.
            base_parser_instance (BaseParser): An instance of the BaseParser for utility methods.
            debug_info_var (tk.BooleanVar): A BooleanVar controlling debug output visibility.
        """
        self.file_tracker = file_tracker_instance
        self.base_parser = base_parser_instance # Keep for utility methods
        self.media_classifier = MediaClassifier() # Initialize MediaClassifier here
        self.debug_info_var = debug_info_var
        self.current_search_thread = None
        self.stop_event = threading.Event()
        print("INFO: FileSearchService instance created.")

    def start_search(self, search_term, search_location, selected_type, exact_match_mode, result_callback, error_callback, completion_callback):
        """
        Starts a file search in a separate thread.

        Args:
            search_term (str): The term to search for.
            search_location (str): The directory to search in.
            selected_type (str): The content type filter ("Movie", "TV Show", "Other", "All").
            exact_match_mode (bool): If True, performs an exact match search.
            result_callback (callable): Callback function to deliver results to the GUI.
            error_callback (callable): Callback function to report errors to the GUI.
            completion_callback (callable): Callback function to signal search completion to the GUI.
        """
        if self.current_search_thread and self.current_search_thread.is_alive():
            print("INFO: A search is already running. Please stop it first.")
            error_callback("A search is already running. Please stop it first.")
            return

        self.stop_event.clear() # Clear any lingering stop signals from previous runs
        self.file_tracker.set_stop_event(self.stop_event) # Pass stop event to file tracker

        self.current_search_thread = threading.Thread(
            target=self._run_search,
            args=(search_term, search_location, selected_type, exact_match_mode, result_callback, error_callback, completion_callback)
        )
        self.current_search_thread.daemon = True # Allow the thread to exit with the main program
        self.current_search_thread.start()
        print("INFO: FileSearchService: Search thread started.")

    def _run_search(self, search_term, search_location, selected_type, exact_match_mode, result_callback, error_callback, completion_callback):
        """
        Internal method to execute the search logic. Runs in a separate thread.
        """
        try:
            # Step 1: Scan all relevant files using FileTracker
            # The FileTracker's scan_files now handles max_depth and excluded_types internally via AppSettings
            all_scanned_files_data = self.file_tracker.search_files(search_term, search_location, selected_type, exact_match_mode) # filetracker returns all scanned files

            if self.stop_event.is_set():
                print("INFO: FileSearchService: Search cancelled during file scanning.")
                completion_callback() # Signal completion even if stopped
                return

            print(f"INFO: FileSearchService: Successfully scanned {len(all_scanned_files_data)} files.")

            # Step 2: Categorize and Filter files
            filtered_results = []
            normalized_search_term_for_comparison = self.base_parser._normalize_string_for_comparison(search_term)
            
            # Pre-parse the search term for TV show components (only for smart search)
            search_season, search_episode, sxe_start_in_search, sxe_end_in_search = self.base_parser.extract_season_episode_from_string(search_term)
            
            # Determine the title part from the search term for smart matching
            normalized_search_title_part = ""
            if not exact_match_mode:
                if sxe_start_in_search != -1:
                    raw_search_title_part = search_term[0:sxe_start_in_search].strip()
                    normalized_search_title_part = self.base_parser._normalize_string_for_comparison(raw_search_title_part)
                else:
                    normalized_search_title_part = normalized_search_term_for_comparison # If no SxE, use full normalized term for title matching


            for file_data in all_scanned_files_data:
                if self.stop_event.is_set():
                    print("INFO: FileSearchService: Search cancelled during classification/filtering.")
                    completion_callback()
                    return

                file_path = file_data['raw_path']
                file_name = os.path.basename(file_path)
                file_name_without_ext, _ = os.path.splitext(file_name)

                # Use MediaClassifier to classify the file
                classified_item = self.media_classifier.classify_and_parse_file(file_path, file_data['size_bytes'])
                
                # Update file_data with classified category and parsed_data
                file_data['category'] = classified_item['category']
                file_data['parsed_data'] = classified_item['parsed_data']


                # --- Apply Filtering Logic (based on exact_match_mode and selected_type) ---
                is_match = False
                if exact_match_mode:
                    # For exact match, match against full filename or base filename directly
                    prepared_search_term = search_term.lower().strip()
                    full_filename_lower = file_name.lower().strip()
                    base_filename_lower = file_name_without_ext.lower().strip()

                    if prepared_search_term == full_filename_lower or \
                       prepared_search_term == base_filename_lower:
                        is_match = True
                else: # Smart search mode
                    # Perform smart matching based on the filename and parsed components
                    is_match = self._perform_smart_match(
                        file_name_without_ext,
                        normalized_search_term_for_comparison,
                        search_season, search_episode, normalized_search_title_part
                    )

                # Apply category filter
                if is_match and (selected_type == "All" or file_data['category'] == selected_type): # Use file_data['category']
                    filtered_results.append(file_data)
                    print(f"DEBUG: FileSearchService: Matched and filtered: {file_name}")

            print(f"INFO: FileSearchService: Finished processing. Found {len(filtered_results)} matching files.")
            result_callback(filtered_results, search_term, selected_type)

        except Exception as e:
            print(f"ERROR: FileSearchService: An unhandled error occurred in search task: {e}")
            error_callback(f"An unexpected error occurred during search: {e}")
        finally:
            completion_callback() # Always signal completion, even on error

    def stop_search(self):
        """Signals the ongoing search thread to stop."""
        self.stop_event.set()
        print("INFO: FileSearchService: Stop event set.")
        # Optionally, wait for the thread to actually finish if needed for stricter control
        # if self.current_search_thread and self.current_search_thread.is_alive():
        #     self.current_search_thread.join(timeout=5) # Wait up to 5 seconds
        #     if self.current_search_thread.is_alive():
        #         print("WARNING: FileSearchService: Search thread did not terminate gracefully.")


    def _perform_smart_match(self, filename_without_ext, normalized_search_term, search_season, search_episode, normalized_search_title_part):
        """
        Applies the 'smart' matching logic, combining title and SxE.
        """
        normalized_filename = self.base_parser._normalize_string_for_comparison(filename_without_ext)

        # Direct substring match (case-insensitive, normalized)
        if normalized_search_term in normalized_filename:
            return True

        # TV Show intelligent matching
        if search_season is not None or normalized_search_title_part:
            parsed_season, parsed_episode, sxe_start_in_file, sxe_end_in_file = self.base_parser.extract_season_episode_from_string(filename_without_ext)

            title_part_from_file = ""
            if sxe_start_in_file != -1:
                title_part_from_file = filename_without_ext[0:sxe_start_in_file].strip()
            else:
                title_part_from_file = filename_without_ext
            normalized_title_part_from_file = self.base_parser._normalize_string_for_comparison(title_part_from_file)

            is_title_match = True
            if normalized_search_title_part: # If search term has a title part before SxE
                if normalized_search_title_part not in normalized_title_part_from_file:
                    is_title_match = False

            is_sxe_match = True
            if search_season is not None:
                search_episodes = []
                if search_episode:
                    for ep_part in search_episode.split('-'):
                        try:
                            search_episodes.append(int(ep_part))
                        except ValueError:
                            pass

                parsed_episodes = []
                if parsed_episode:
                    for ep_part in parsed_episode.split('-'):
                        try:
                            parsed_episodes.append(int(ep_part))
                        except ValueError:
                            pass

                if parsed_season != search_season or parsed_episode is None or not any(s_ep in parsed_episodes for s_ep in search_episodes):
                    is_sxe_match = False

            # If search term has SxE or a title part before SxE, both must match.
            # If search term has neither, then only direct substring match applies (already handled above).
            if (search_season is not None or normalized_search_title_part):
                return is_title_match and is_sxe_match

        return False # No match found by any criteria

