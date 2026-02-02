import re
from base_parser import BaseParser

class TvShowParser(BaseParser):
    def __init__(self):
        super().__init__()
        print("INFO: TvShowParser instance created.")

    def parse_tv_show_filename(self, filename_without_ext):
        """
        Parses a TV show filename based on common naming conventions (SxxExx or year-based).

        Args:
            filename_without_ext (str): The filename string without its extension.

        Returns:
            dict: Parsed TV show metadata.
        """
        parsed_data = {
            "type": "TV Show",
            "title": None, # Will be determined more precisely
            "season": None,
            "episode": None,
            "episode_title": None,
            "resolution": None,
            "source": None,
            "video_format": None,
            "audio_format": None,
            "group_tag": None,
            "version": None,
            "original_filename": filename_without_ext
        }

        temp_filename = filename_without_ext # Use a temporary string for cleaning

        # 1. Extract Season and Episode first using helper from BaseParser
        season_num, episode_str, sxe_start, sxe_end = self.extract_season_episode_from_string(temp_filename)

        if season_num is not None and episode_str is not None:
            parsed_data["season"] = season_num
            parsed_data["episode"] = episode_str

            # Attempt to extract title based on SxxExx position
            title_part_before_sxe = temp_filename[:sxe_start].strip()
            
            # Episode title is the part immediately after SxxExx and before other tags
            post_sxe_part = temp_filename[sxe_end:].strip()
            
            # Remove common delimiters at the very start of post_sxe_part (like a leading dot or space)
            if post_sxe_part and (post_sxe_part[0] == '.' or post_sxe_part[0] == '-'):
                post_sxe_part = post_sxe_part[1:].strip()

            episode_title_candidate = self._clean_string_of_all_tags(post_sxe_part)
            
            # Check if what's left is a meaningful episode title or just a common tag/empty
            # We explicitly want to avoid group names like "KILLERS" being episode titles
            if episode_title_candidate and episode_title_candidate not in ["hdtv", "webrip", "bluray", "x264", "x265", "killers", "proper", "repack"]:
                parsed_data["episode_title"] = episode_title_candidate
            else:
                parsed_data["episode_title"] = None # If it's just tags or empty, don't set as episode title

            # Now, clean the title part that came before SxxExx
            # This is done *after* potential episode title extraction to avoid interference
            parsed_data["title"] = self._clean_string_of_all_tags(title_part_before_sxe)
            
        else: # No SxxExx pattern, might be a daily show or other format
            # Try to extract year (e.g., for "The Daily Show 2023 10 26")
            year = self.extract_year_from_string(temp_filename)
            if year:
                parsed_data["year"] = year
                # For daily shows, the title is usually everything before the date
                # Simple heuristic: remove date and then clean
                cleaned_title_candidate = re.sub(r'\b\d{4}[.\s-]?\d{2}[.\s-]?\d{2}\b', '', temp_filename, flags=re.IGNORECASE).strip()
                parsed_data["title"] = self._clean_string_of_all_tags(cleaned_title_candidate)
            else:
                # If no SxxExx and no clear date, assume the whole filename (after general cleaning) is the title
                parsed_data["title"] = self._clean_string_of_all_tags(temp_filename)


        # Extract other common metadata from the FULL original filename, but ensure title is already set
        # These patterns are applied to the full filename to catch tags anywhere
        group_match = self.group_tag_pattern.search(temp_filename)
        if group_match: parsed_data["group_tag"] = group_match.group(1)

        resolution_match = self.resolution_pattern.search(temp_filename)
        if resolution_match: parsed_data["resolution"] = resolution_match.group(0)

        source_match = self.source_pattern.search(temp_filename)
        if source_match: parsed_data["source"] = source_match.group(0)

        video_match = self.video_format_pattern.search(temp_filename)
        if video_match: parsed_data["video_format"] = video_match.group(0)

        audio_match = self.audio_format_pattern.search(temp_filename)
        if audio_match: parsed_data["audio_format"] = audio_match.group(0)

        version_match = self.version_pattern.search(temp_filename)
        if version_match: parsed_data["version"] = version_match.group(0)
        
        language_match = self.language_pattern.search(temp_filename)
        if language_match: parsed_data["language"] = language_match.group(0)

        bit_depth_match = self.bit_depth_pattern.search(temp_filename)
        if bit_depth_match: parsed_data["bit_depth"] = bit_depth_match.group(0)

        hdr_match = self.hdr_pattern.search(temp_filename)
        if hdr_match: parsed_data["hdr"] = hdr_match.group(0)

        # Final normalization ensures consistency for the main title
        if parsed_data["title"]:
            parsed_data["title"] = self._normalize_string_for_comparison(parsed_data["title"])
        else:
            # Fallback if title is still None, clean the whole filename as title
            parsed_data["title"] = self._normalize_string_for_comparison(filename_without_ext)

        return parsed_data