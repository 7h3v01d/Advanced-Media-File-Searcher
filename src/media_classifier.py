import os
import re
from movie_parser import MovieParser
from tv_show_parser import TvShowParser
from base_parser import BaseParser # Import BaseParser for its static methods

class MediaClassifier:
    def __init__(self):
        print("INFO: MediaClassifier instance created.")
        self.movie_parser = MovieParser()
        self.tv_show_parser = TvShowParser()

    def classify_and_parse_file(self, file_path, file_size_bytes):
        """
        Classifies a file as Movie, TV Show, or Other, and parses its filename using dedicated parsers.

        Args:
            file_path (str): The full path to the file.
            file_size_bytes (int): The size of the file in bytes.

        Returns:
            dict: A dictionary containing:
                  - "category": "Movie", "TV Show", or "Other"
                  - "raw_path": The original full file path.
                  - "size_bytes": The file size in bytes.
                  - "parsed_data": A dictionary with metadata (specific to category)
                                   or just the original filename if "Other".
        """
        base_name = os.path.basename(file_path)
        filename_without_ext, file_extension = os.path.splitext(base_name)

        result = {
            "category": "Other",
            "raw_path": file_path,
            "size_bytes": file_size_bytes,
            "parsed_data": {"original_filename": base_name} # Default for "Other"
        }

        # Try to parse as TV Show first (more specific patterns often apply)
        tv_show_data = self.tv_show_parser.parse_tv_show_filename(filename_without_ext)
        if tv_show_data["season"] is not None and tv_show_data["episode"] is not None:
            result["category"] = "TV Show"
            result["parsed_data"] = tv_show_data
            return result

        # Try to parse as Movie
        movie_data = self.movie_parser.parse_movie_filename(filename_without_ext)
        # Heuristic for movie: if year OR resolution OR source OR video format is found
        if (movie_data["year"] is not None or
            movie_data["resolution"] is not None or
            movie_data["source"] is not None or
            movie_data["video_format"] is not None):
            result["category"] = "Movie"
            result["parsed_data"] = movie_data
            return result

        print(f"INFO: Classified '{base_name}' as 'Other'.")
        return result

    def categorize_and_process_results(self, raw_search_results):
        """
        Takes raw search results from FileTracker and categorizes/parses them.

        Args:
            raw_search_results (list): List of dictionaries from FileTracker:
                                       [{"path": "...", "size_bytes": ...}, ...]

        Returns:
            list: List of processed dictionaries with category and parsed_data.
        """
        processed_results = []
        print(f"INFO: Starting to categorize and parse {len(raw_search_results)} raw search results.")
        for item in raw_search_results:
            processed_results.append(self.classify_and_parse_file(item["path"], item["size_bytes"]))
        print(f"INFO: Finished categorizing and parsing results.")
        return processed_results

