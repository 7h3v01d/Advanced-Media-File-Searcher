import re
from base_parser import BaseParser

class MovieParser(BaseParser):
    def __init__(self):
        super().__init__()
        print("INFO: MovieParser instance created.")

    def parse_movie_filename(self, filename_without_ext):
        """
        Parses a movie filename based on common naming conventions.

        Args:
            filename_without_ext (str): The filename string without its extension.

        Returns:
            dict: Parsed movie metadata.
        """
        parsed_data = {
            "type": "Movie",
            "title": filename_without_ext, # Default title
            "year": None,
            "resolution": None,
            "source": None,
            "video_format": None,
            "audio_format": None,
            "group_tag": None,
            "version": None,
            "original_filename": filename_without_ext
        }

        # Extract metadata first from the original filename using compiled patterns from BaseParser
        group_match = self.group_tag_pattern.search(filename_without_ext)
        if group_match:
            parsed_data["group_tag"] = group_match.group(1)

        year_match = self.year_pattern.search(filename_without_ext)
        if year_match:
            parsed_data["year"] = year_match.group(1)

        resolution_match = self.resolution_pattern.search(filename_without_ext)
        if resolution_match: parsed_data["resolution"] = resolution_match.group(0) # group(0) for full match

        source_match = self.source_pattern.search(filename_without_ext)
        if source_match: parsed_data["source"] = source_match.group(0)

        video_match = self.video_format_pattern.search(filename_without_ext)
        if video_match: parsed_data["video_format"] = video_match.group(0)

        audio_match = self.audio_format_pattern.search(filename_without_ext)
        if audio_match: parsed_data["audio_format"] = audio_match.group(0)

        version_match = self.version_pattern.search(filename_without_ext)
        if version_match: parsed_data["version"] = version_match.group(0)

        # The core title is what remains after all common metadata tags are removed and normalized
        parsed_data["title"] = self._clean_string_of_all_tags(filename_without_ext)

        return parsed_data
