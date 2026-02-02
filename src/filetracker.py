import os
import re
import sys
from base_parser import BaseParser # Import BaseParser

class FileTracker(BaseParser): # Inherit from BaseParser
    def __init__(self):
        super().__init__() # Initialize BaseParser's attributes (like regex patterns)
        print("INFO: FileTracker instance created.")

    def find_file(self, search_term, search_location, stop_event, exact_match=False): # Added exact_match parameter
        """
        Searches for files within a given directory and its subdirectories
        using intelligent matching based on filename structure.

        Args:
            search_term (str): The term to search for (e.g., "Game of Thrones S04E04", "game of s04e04", "My Movie").
            search_location (str): The starting directory for the search.
            stop_event (threading.Event): An event object to signal search termination.
            exact_match (bool): If True, performs a literal (case-insensitive) match
                                 without normalizing separators or cleaning tags.
                                 If False, performs the enhanced smart search.

        Returns:
            list: A list of dictionaries, each containing 'path' and 'size_bytes'
                  for matching files. Returns an empty list if no matches found.
                  Returns partial results if stopped by stop_event.
        """
        found_files = []

        print(f"INFO: Starting file search in '{search_location}' for term '{search_term}'.")
        print(f"DEBUG: (FileTracker.find_file) Exact match mode requested: {exact_match}")
        print(f"DEBUG: (FileTracker.find_file) Raw search term received: '{search_term}'")


        # Prepare search term based on exact_match flag
        if exact_match:
            # For exact match, the search term is always lowercased and stripped.
            # We will attempt to match this prepared_search_term against both
            # the full file name and the file's base name.
            prepared_search_term = search_term.lower().strip()
            print(f"DEBUG: (FileTracker.find_file) Prepared search term for EXACT comparison: '{prepared_search_term}'")
            
            # For exact matches, we don't need the TV show parsing upfront
            search_season, search_episode, sxe_start_in_search, sxe_end_in_search = (None, None, -1, -1)
            normalized_search_title_part = "" # Not used for exact match, but initialized for consistency
        else:
            # Original "smart" search normalization and TV show parsing (unchanged)
            normalized_search_term = self._normalize_string_for_comparison(search_term)
            print(f"DEBUG: (FileTracker.find_file) Performing SMART match search. Normalized search term: '{normalized_search_term}'")

            # Pre-parse the search term for TV show components (only for smart search)
            search_season, search_episode, sxe_start_in_search, sxe_end_in_search = self.extract_season_episode_from_string(search_term)

            if sxe_start_in_search != -1:
                raw_search_title_part = search_term[0:sxe_start_in_search].strip()
                normalized_search_title_part = self._normalize_string_for_comparison(raw_search_title_part)
            else:
                normalized_search_title_part = normalized_search_term # If no SxE, use full normalized term for title matching

            if search_season is not None:
                print(f"DEBUG: (FileTracker.find_file) Search term contains SxE: Season {search_season}, Episode {search_episode}.")
                if normalized_search_title_part:
                    print(f"DEBUG: (FileTracker.find_file) Normalized Title Part (before SxE) from search term: '{normalized_search_title_part}'")


        # Check if the search_location is a valid directory
        if not os.path.isdir(search_location):
            print(f"ERROR: Search location '{search_location}' is not a valid directory.")
            return []

        # Define system/temporary file extensions to always exclude
        # Common content extensions like .txt, .jpg, .png, .srt, .sub, .nfo, .url are NO LONGER excluded here
        # because the 'Other' category or a specific content filter should handle them.
        system_file_extensions_to_exclude = ['.db', '.ini', '.DS_Store', '.git', '.log']


        # Iterate through directory using os.walk
        for root, dirs, files in os.walk(search_location):
            # Checking for stop signal at the start of each directory iteration
            if stop_event.is_set():
                print(f"INFO: Search stopped prematurely by user request in directory: {root}")
                return found_files # Return files found so far

            for file in files:
                file_path = os.path.join(root, file)

                if stop_event.is_set():
                    print(f"INFO: Search stopped prematurely by user request while processing files in: {root}")
                    return found_files # Return files found so far

                filename_without_ext, file_extension = os.path.splitext(file)
                full_filename_lower = file.lower().strip() # e.g., "movie.title.mkv"
                base_filename_lower = filename_without_ext.lower().strip() # e.g., "movie.title"

                # Exclude truly uninteresting system/hidden files regardless of search type
                if file_extension.lower() in system_file_extensions_to_exclude or file.startswith('.'):
                    print(f"DEBUG: Skipping system/hidden file: '{file}'")
                    continue 

                # Ensure it's a file and not a broken symlink or other non-regular file system entry
                if not os.path.isfile(file_path):
                    continue

                try:
                    file_size_bytes = os.path.getsize(file_path)
                except OSError as e:
                    print(f"ERROR: Could not get size for file {file_path}: {e}")
                    file_size_bytes = -1 # Indicate size could not be retrieved


                # --- Search Logic Branching ---
                if exact_match:
                    match_found = False

                    # Attempt 1: Match against the full filename (including its extension)
                    if prepared_search_term == full_filename_lower:
                        match_found = True
                        print(f"DEBUG: EXACT match FOUND (Full Name) for:\n"
                              f"  Search: '{search_term}'\n"
                              f"  File: '{file_path}'")
                    
                    # Attempt 2: Match against the base filename (excluding its extension)
                    # This is important for cases where the user omits the extension or for companion files.
                    if not match_found and prepared_search_term == base_filename_lower:
                        match_found = True
                        print(f"DEBUG: EXACT match FOUND (Base Name) for:\n"
                              f"  Search: '{search_term}'\n"
                              f"  File: '{file_path}' (matching base name)")

                    if match_found:
                        found_files.append({"path": file_path, "size_bytes": file_size_bytes})
                        continue # Move to next file
                    else:
                        print(f"DEBUG: EXACT match FAILED for:\n"
                              f"  Search: '{prepared_search_term}'\n"
                              f"  File Full:   '{full_filename_lower}'\n"
                              f"  File Base:   '{base_filename_lower}'\n"
                              f"  Path: '{file_path}'")
                else:
                    # Original "smart" search logic (remains unchanged as it's working well)
                    normalized_filename = self._normalize_string_for_comparison(filename_without_ext)
                    print(f"DEBUG:   Smart Search: Normalized filename for '{file}': '{normalized_filename}'")


                    # Direct match for simple cases (part of smart search)
                    if normalized_search_term in normalized_filename:
                        print(f"DEBUG: Smart Search: Direct substring match found for '{normalized_search_term}' in '{normalized_filename}' ('{file_path}').")
                        found_files.append({"path": file_path, "size_bytes": file_size_bytes})
                        continue # Move to next file
                    else:
                        pass # Continue to intelligent match if direct fails

                    # More intelligent matching for TV shows (SxxExx and episode titles)
                    # This block only executes if not an exact match AND no direct normalized substring match was found above
                    if search_season is not None or normalized_search_title_part:
                        # Attempt to parse filename as TV show
                        parsed_season, parsed_episode, sxe_start_in_file, sxe_end_in_file = self.extract_season_episode_from_string(filename_without_ext)

                        title_part_from_file = ""
                        if sxe_start_in_file != -1:
                            # Extract title part before SxxExx from the file's name
                            title_part_from_file = filename_without_ext[0:sxe_start_in_file].strip()
                        else:
                            # If no SxE in file, use the whole filename (cleaned) as the title part
                            title_part_from_file = filename_without_ext

                        normalized_title_part_from_file = self._normalize_string_for_comparison(title_part_from_file)

                        is_title_match = True
                        if normalized_search_title_part: # If search term has a title part before SxE
                            if normalized_search_title_part not in normalized_title_part_from_file:
                                is_title_match = False
                                print(f"DEBUG:   Smart Search: Title part '{normalized_search_title_part}' NOT found in file title part '{normalized_title_part_from_file}'.")
                            else:
                                print(f"DEBUG:   Smart Search: Title part '{normalized_search_title_part}' found in file title part '{normalized_title_part_from_file}'.")
                        else:
                             print(f"DEBUG:   Smart Search: No specific title part in search term for '{file}', skipping title match check.")


                        is_sxe_match = True
                        if search_season is not None: # Only check SxE match if search term has season/episode
                            # Parse episodes from search term (can be range like '04-05')
                            search_episodes = []
                            if search_episode:
                                for ep_part in search_episode.split('-'):
                                    try:
                                        search_episodes.append(int(ep_part))
                                    except ValueError:
                                        pass # Ignore invalid episode numbers

                            # Parse episodes from file name
                            parsed_episodes = []
                            if parsed_episode:
                                for ep_part in parsed_episode.split('-'):
                                    try:
                                        parsed_episodes.append(int(ep_part))
                                    except ValueError:
                                        pass # Ignore invalid episode numbers

                            if parsed_season != search_season:
                                is_sxe_match = False
                                print(f"DEBUG:   Smart Search: SxE mismatch (Season). Search S:{search_season}, File S:{parsed_season} for '{file}'.")
                            elif parsed_episode is None or not any(s_ep in parsed_episodes for s_ep in search_episodes):
                                is_sxe_match = False
                                print(f"DEBUG:   Smart Search: SxE mismatch (Episode). Search E:{search_episodes}, File E:{parsed_episodes} for '{file}'.")
                            else:
                                print(f"DEBUG:   Smart Search: SxE match found. Search S:{search_season} E:{search_episodes}, File S:{parsed_season} E:{parsed_episodes}.")
                        else:
                            print(f"DEBUG:   Smart Search: No SxE in search term, skipping SxE match check for this file.")
                            
                        
                        # Final check for intelligent match (combining title and SxE)
                        if is_title_match and is_sxe_match and (search_season is not None or normalized_search_title_part):
                            print(f"DEBUG: Intelligent match found for '{search_term}' (original) in '{file_path}'.")
                            found_files.append({"path": file_path, "size_bytes": file_size_bytes})
                            continue # Move to next file
                        else:
                            pass # Continue to next file if intelligent match fails

        return found_files

# --- Test cases (moved to a separate test script or removed from main for GUI) ---
if __name__ == '__main__':
    # This block is typically for standalone testing of FileTracker, not for GUI execution.
    # It's usually good practice to keep main application logic separate from test cases.
    # For now, it's commented out to avoid confusion when running the GUI.
    pass
