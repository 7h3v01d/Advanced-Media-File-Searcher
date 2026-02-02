import threading
import os
import re
import sys
import time

from filetracker import FileTracker
from media_classifier import MediaClassifier
from base_parser import BaseParser # For utility methods like extract_season_episode_from_string

class FileSearchService:
    """
    A service class that encapsulates the core file search and media classification logic.
    It runs search operations in a separate thread and communicates results via callbacks.
    """
    def __init__(self):
        print("INFO: FileSearchService instance created.")
        self.tracker = FileTracker()
        self.classifier = MediaClassifier()
        self.stop_event = threading.Event()
        self.search_thread = None # To hold the reference to the active search thread

    def start_search(self, search_term, search_location, selected_type, exact_match_mode, result_callback, error_callback, completion_callback):
        """
        Initiates the file search and classification process in a separate thread.

        Args:
            search_term (str): The term to search for.
            search_location (str): The directory to search within.
            selected_type (str): The media type to filter by ("Movie", "TV Show", "Other", "All").
            exact_match_mode (bool): True for exact filename match, False for smart search.
            result_callback (callable): Function to call with processed results.
            error_callback (callable): Function to call if an error occurs.
            completion_callback (callable): Function to call when search completes (success/failure).
        """
        if self.search_thread and self.search_thread.is_alive():
            print("WARNING: Search is already running. Please wait or stop the current search.")
            error_callback("A search is already in progress.")
            return

        self.stop_event.clear() # Clear any previous stop signals
        self.search_thread = threading.Thread(
            target=self._run_search_task,
            args=(search_term, search_location, selected_type, exact_match_mode, result_callback, error_callback, completion_callback)
        )
        self.search_thread.daemon = True # Allows the main program to exit even if this thread is running
        self.search_thread.start()
        print("INFO: Search thread started.")

    def stop_search(self):
        """Signals the running search thread to stop."""
        self.stop_event.set()
        print("INFO: Stop signal sent to search thread.")

    def _run_search_task(self, search_term, search_location, selected_type, exact_match_mode, result_callback, error_callback, completion_callback):
        """
        The actual search logic executed in the separate thread.
        Communicates back to the GUI via provided callback functions.
        """
        try:
            print(f"INFO: Search service: Starting search for '{search_term}' in '{search_location}'.")
            
            # Step 1: Find raw files using FileTracker
            raw_found_files = self.tracker.find_file(search_term, search_location, self.stop_event, exact_match=exact_match_mode)

            if self.stop_event.is_set():
                print("INFO: Search service: FileTracker search was terminated.")
                return # Exit early if stopped

            # Step 2: Categorize and parse raw results using MediaClassifier
            print("INFO: Search service: Categorizing and parsing found files...")
            categorized_results = self.classifier.categorize_and_process_results(raw_found_files)

            if self.stop_event.is_set():
                print("INFO: Search service: MediaClassifier processing was terminated.")
                return # Exit early if stopped

            # Step 3: Apply GUI-level filtering based on selected_type and exact_match_mode
            final_filtered_results = []
            
            if exact_match_mode:
                # In exact match mode, FileTracker has already ensured filenames match exactly.
                # Here, we only filter by the selected category (Movie, TV Show, Other, All).
                for item in categorized_results:
                    if self.stop_event.is_set(): # Check stop event during filtering
                        print("INFO: Search service: Filtering terminated by user.")
                        break
                    
                    if selected_type == "All" or item["category"] == selected_type:
                        print(f"DEBUG: Search service: Exact Match Mode: Adding '{item['raw_path']}' (Category: {item['category']}) to results as it matches filter '{selected_type}'.")
                        final_filtered_results.append(item)
                    else:
                        print(f"DEBUG: Search service: Exact Match Mode: Skipping '{item['raw_path']}' (Category: {item['category']}) as it does not match filter '{selected_type}'.")
                print(f"DEBUG: Search service: Exact match mode. Final results after category filter: {len(final_filtered_results)}.")
            else:
                # This is the original "smart search" filtering logic based on parsed components.
                if selected_type == "TV Show":
                    search_season, search_episode, _, _ = BaseParser.extract_season_episode_from_string(search_term)
                    # Clean the search term's title part for smart TV show matching
                    search_term_without_sxe = re.sub(r'[Ss]\d{1,2}[Ee]\d{1,2}(?:-\d{1,2})?', '', search_term, flags=re.IGNORECASE).strip()
                    normalized_search_title_part = self.classifier.tv_show_parser._clean_string_of_all_tags(
                        search_term_without_sxe
                    )
                    print(f"DEBUG: Search service: Smart Search (TV Show filter). Cleaned Search Title Part: '{normalized_search_title_part}', Season: {search_season}, Episode: {search_episode}")

                    for item in categorized_results:
                        if self.stop_event.is_set(): # Check stop event during filtering
                            print("INFO: Search service: Filtering terminated by user.")
                            break

                        if item["category"] == "TV Show":
                            parsed_data = item["parsed_data"]
                            is_title_match = True
                            is_sxe_match = True
                            
                            print(f"DEBUG: Search service: Processing TV Show item for Smart Search: {os.path.basename(item['raw_path'])}")
                            print(f"DEBUG:   Search service: Parsed Title: '{parsed_data.get('title')}', Season: {parsed_data.get('season')}, Episode: {parsed_data.get('episode')}")

                            if normalized_search_title_part:
                                normalized_parsed_title = BaseParser._normalize_string_for_comparison(parsed_data.get('title', ''))
                                if normalized_search_title_part not in normalized_parsed_title:
                                    is_title_match = False
                                    print(f"DEBUG:   Search service: Title part '{normalized_search_title_part}' NOT found in parsed title '{normalized_parsed_title}'.")
                                else:
                                    print(f"DEBUG:   Search service: Title part '{normalized_search_title_part}' found in parsed title '{normalized_parsed_title}'.")
                            else:
                                print("DEBUG:   Search service: No specific search title part provided for TV show, skipping title match check.")
                            
                            if search_season is not None:
                                parsed_season = parsed_data.get("season")
                                parsed_episode = parsed_data.get("episode") 

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

                                if parsed_season != search_season:
                                    is_sxe_match = False
                                    print(f"DEBUG:   Search service: SxE mismatch (Season). Search S:{search_season}, Parsed S:{parsed_season}.")
                                elif parsed_episode is None or not any(s_ep in parsed_episodes for s_ep in search_episodes):
                                    is_sxe_match = False
                                    print(f"DEBUG:   Search service: SxE mismatch (Episode). Search E:{search_episodes}, Parsed E:{parsed_episodes}.")
                                else:
                                    print(f"DEBUG:   Search service: SxE match found. Search S:{search_season} E:{search_episodes}, Parsed S:{parsed_season} E:{parsed_episodes}.")
                            else:
                                print("DEBUG:   Search service: No SxE in search term, skipping SxE match check for this file.")
                            
                            if is_title_match or is_sxe_match: 
                                final_filtered_results.append(item)
                            else:
                                print(f"DEBUG: Search service: TV Show item '{os.path.basename(item['raw_path'])}' did not match by title or SxE.")

                else: # For Movie, Other, or All in smart search mode (simple category filter)
                    for item in categorized_results:
                        if self.stop_event.is_set(): # Check stop event during filtering
                            print("INFO: Search service: Filtering terminated by user.")
                            break
                        if selected_type == "All" or item["category"] == selected_type:
                            final_filtered_results.append(item)
                print(f"DEBUG: Search service: Smart search mode. Final results after category filter: {len(final_filtered_results)}.")

            # Call the GUI's result callback
            result_callback(final_filtered_results, search_term, selected_type)

        except Exception as e:
            print(f"ERROR: Search service: An unhandled error occurred in search task: {e}", file=sys.stderr)
            error_callback(f"An error occurred during search: {e}")
        finally:
            self.stop_event.clear() # Always clear the stop event at the end of a task
            completion_callback() # Signal completion to the GUI
            print("INFO: Search service: Search task completed.")

