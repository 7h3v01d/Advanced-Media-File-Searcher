import re
import os

class BaseParser:
    def __init__(self):
        # print("INFO: BaseParser instance created. Initializing common regex patterns.")
        self.year_pattern = re.compile(r'\b(\d{4})\b')
        self.resolution_pattern = re.compile(r'\b(480p|700p|720p|1080p|1440p|2160p|4k|8k)\b', re.IGNORECASE)
        self.source_pattern = re.compile(r'\b(WEB-DL|WEBRip|BluRay|BDRip|DVDRip|HDRip|HDTV|DVD|VOD|DDC|CAM|TS|R5|WP|SCR)\b', re.IGNORECASE)
        self.video_format_pattern = re.compile(r'\b(x264|x265|HEVC|H\.264|H\.265|VP9|AV1|XviD|DivX)\b', re.IGNORECASE)
        self.audio_format_pattern = re.compile(r'\b(AC3|DTS|DTS-HD|TrueHD|Atmos|DD5\.1|AAC|MP3)\b', re.IGNORECASE)
        # More robust group tag pattern: handles typical bracketed or hyphenated end tags
        self.group_tag_pattern = re.compile(r'[-_. ]?(\[?[A-Za-z0-9_.-]+\]?)$', re.IGNORECASE)
        self.version_pattern = re.compile(r'\b(PROPER|REPACK|RERIP|EXTENDED|UNCUT|UNRATED|DIRECTORS.CUT|REMASTERED|COLLECTORS.EDITION)\b', re.IGNORECASE)
        self.language_pattern = re.compile(r'\b(eng|ita|fre|deu|jpn|kor|spa|rus)(?:dub|sub)?\b', re.IGNORECASE)
        self.bit_depth_pattern = re.compile(r'\b(8bit|10bit|12bit)\b', re.IGNORECASE)
        self.hdr_pattern = re.compile(r'\b(HDR|HDR10|DolbyVision|DV)\b', re.IGNORECASE)
        self.repack_pattern = re.compile(r'\b(REPACK|PROPER)\b', re.IGNORECASE)

    @staticmethod
    def _normalize_string_for_comparison(text):
        """
        Normalizes a string for comparison by:
        - Converting to lowercase.
        - Replacing common separators (dots, underscores, hyphens) with spaces.
        - Collapsing multiple spaces into a single space and stripping leading/trailing spaces.
        """
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[._-]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def extract_season_episode_from_string(text):
        """
        Extracts SxxExx pattern from a string (e.g., "S01E02", "s1e2", "s01e02-e03").
        Returns (season_int, episode_str, match_start_index, match_end_index) if found, else (None, None, -1, -1).
        The indices help in splitting the string accurately.
        """
        match = re.search(r'\b[Ss](\d{1,2})[Ee](\d{1,2}(?:-\d{1,2})?)\b', text, re.IGNORECASE)
        if match:
            try:
                season = int(match.group(1))
            except ValueError:
                season = None
            episode = match.group(2)
            return season, episode, match.start(), match.end()
        return None, None, -1, -1
    
    @staticmethod
    def extract_year_from_string(text):
        """Extracts a 4-digit year from a string."""
        match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
        if match:
            return int(match.group(1))
        return None

    def _clean_string_of_all_tags(self, text):
        """
        Removes all common metadata tags (year, resolution, source, format, group, version, etc.)
        from a string to derive a cleaner title or episode name.
        """
        cleaned_text = text
        
        # Apply more specific pattern removals first, then general group tag
        patterns = [
            self.year_pattern,
            self.resolution_pattern,
            self.source_pattern,
            self.video_format_pattern,
            self.audio_format_pattern,
            self.version_pattern,
            self.language_pattern,
            self.bit_depth_pattern,
            self.hdr_pattern,
            self.repack_pattern,
            # Add other specific patterns here before the general group tag
        ]

        for pattern in patterns:
            cleaned_text = pattern.sub('', cleaned_text)
        
        # After specific patterns, then attempt to remove the general group tag, which is often at the end
        # The group_tag_pattern might also remove hyphen/dot/space before it if it exists.
        cleaned_text = self.group_tag_pattern.sub('', cleaned_text)

        # After removing specific patterns, clean common delimiters and collapse spaces
        cleaned_text = self._normalize_string_for_comparison(cleaned_text)
        return cleaned_text