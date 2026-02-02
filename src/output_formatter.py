import os
from gui_utilities import format_bytes

class OutputFormatter:
    """
    Handles the formatting of search results for display in the GUI's Text widgets.
    Ensures consistent alignment, spacing, and conditional display (e.g., debug info).
    Returns a list of (text_segment, tag_name) tuples for inserting into a Tkinter Text widget.
    """

    @staticmethod
    def _format_item_details(item_data, debug_info_enabled):
        """
        Helper method to format details of a single file item.
        Includes conditional display of parsed data based on debug mode.
        Returns a list of (text_segment, tag_name) tuples.
        """
        segments = []
        # Separate "File: " from the actual filename and assign different tags
        segments.append((f"      File: ", "item_detail")) # "File: " part uses item_detail tag
        segments.append((f"{os.path.basename(item_data['raw_path'])}\n", "item_filename_result")) # Filename uses new tag
        
        # Truncate path to show only directory, but still keep 'item_detail' tag for styling
        dir_path = os.path.dirname(item_data['raw_path'])
        segments.append((f"      Path: {dir_path}\n", "item_detail"))
        
        segments.append((f"      Size: {format_bytes(item_data['size_bytes'])}\n", "item_detail"))
        segments.append((f"      Category: {item_data['category']}\n", "item_detail"))

        # Display 'Parsed' data only if debug is enabled
        if debug_info_enabled:
            parsed_data = item_data.get("parsed_data", {})
            if parsed_data: # Ensure there's actual parsed data
                # Format parsed data: type='Movie', title='...', etc.
                parsed_info_str = ", ".join([f"{k}='{v}'" for k, v in parsed_data.items()])
                segments.append((f"      Parsed: {parsed_info_str}\n", "item_detail_parsed"))
            else:
                segments.append((f"      Parsed: No detailed parsing data available.\n", "item_detail_parsed"))
        return segments

    @staticmethod
    def format_single_search_results(results, search_term, selected_type, debug_info_var):
        """
        Formats the results of a single search for display.
        Returns a list of (text_segment, tag_name) tuples.

        Args:
            results (list): List of dictionaries, each representing a found file.
            search_term (str): The original search term.
            selected_type (str): The filter type used (e.g., "Movie", "TV Show", "All").
            debug_info_var (tk.BooleanVar): The BooleanVar controlling debug output.

        Returns:
            list: A list of (text_segment, tag_name, raw_path_for_item) tuples ready for display.
                  Each segment might also carry a unique item ID to link back to raw data.
        """
        segments = []
        debug_info_enabled = debug_info_var.get()

        # Add main summary header
        if results:
            segments.append(("\n--- Search Summary ---\n\n", "summary_header_bold_large", None))
            segments.append((f"Search Term: '{search_term}'\n", "item_detail", None))
            segments.append((f"Filter Type: '{selected_type}'\n\n", "item_detail", None))
            
            for item in results:
                item_segments = OutputFormatter._format_item_details(item, debug_info_enabled)
                # Mark the first segment of the item with its raw_path for later retrieval
                if item_segments:
                    # The raw_path is now tied to the second segment (the actual filename)
                    segments.append((item_segments[0][0], item_segments[0][1], None)) # "File: " part
                    segments.append((item_segments[1][0], item_segments[1][1], item['raw_path'])) # Filename part with path
                    for segment_text, segment_tag in item_segments[2:]: # Start from 2nd index for remaining details
                        segments.append((segment_text, segment_tag, None))
                segments.append(("\n", "", None)) # Add newline between items with no specific path attachment
            
            # Add overall search statistics footer
            segments.append(("--- Overall Search Statistics ---\n", "category_header", None))
            segments.append((f"Total files found: {len(results)}\n", "item_detail", None))

        else:
            segments.append(("\n--- Search Summary: No Results ---\n\n", "summary_header_bold_large", None))
            segments.append((f"Search Term: '{search_term}'\n", "item_detail", None))
            segments.append((f"Filter Type: '{selected_type}'\n\n", "item_detail", None))
            segments.append((f"No '{selected_type}' files found matching '{search_term}'.\n", "summary_not_found", None))
            segments.append(("\n--- Overall Search Statistics ---\n", "category_header", None))
            segments.append((f"Total files found: 0\n", "item_detail", None))
        
        return segments


    @staticmethod
    def format_batch_search_results(all_batch_results, was_stopped, debug_info_var):
        """
        Formats the aggregated results of a batch search for display.
        Returns a list of (text_segment, tag_name, raw_path_for_item) tuples.

        Args:
            all_batch_results (list): List of dictionaries, each representing the outcome
                                      for a single term in the batch.
            was_stopped (bool): True if the batch process was manually stopped, False otherwise.
            debug_info_var (tk.BooleanVar): The BooleanVar controlling debug output.

        Returns:
            list: A list of (text_segment, tag_name, raw_path_for_item) tuples ready for display.
        """
        segments_with_paths = []
        debug_info_enabled = debug_info_var.get()

        if was_stopped:
            segments_with_paths.append(("--- Batch Process: STOPPED by User ---\n\n", "summary_header_bold_large", None))
        else:
            segments_with_paths.append(("--- Batch Process Summary ---\n\n", "summary_header_bold_large", None))

        total_files_found = 0
        total_terms_processed = len(all_batch_results)
        terms_with_results = 0

        for i, batch_item in enumerate(all_batch_results):
            term = batch_item['term']
            results_for_term = batch_item['results']
            filter_type = batch_item['filter_type']
            exact_match = batch_item['exact_match']
            status = batch_item['status']
            error_message = batch_item.get('error_message', '')

            # Add a separator and term details
            segments_with_paths.append((f"[{i+1}/{total_terms_processed}] Term: '{term}' (Filter: {filter_type}, Exact Match: {exact_match})\n", "category_header", None))

            if status == 'error':
                segments_with_paths.append((f"  Status: ERROR - {error_message}\n", "error", None))
            elif status == 'completed' and results_for_term:
                segments_with_paths.append((f"  Found {len(results_for_term)} items.\n", "summary_found", None))
                total_files_found += len(results_for_term)
                terms_with_results += 1
                for item in results_for_term:
                    item_segments = OutputFormatter._format_item_details(item, debug_info_enabled)
                    if item_segments:
                        # The raw_path is now tied to the second segment (the actual filename)
                        segments_with_paths.append((item_segments[0][0], item_segments[0][1], None)) # "File: " part
                        segments_with_paths.append((item_segments[1][0], item_segments[1][1], item['raw_path'])) # Filename part with path
                        for segment_text, segment_tag in item_segments[2:]: # Start from 2nd index for remaining details
                            segments_with_paths.append((segment_text, segment_tag, None)) # Subsequent lines don't need raw_path
            else: # No results found
                segments_with_paths.append(("  No results found for this term.\n", "summary_not_found", None))
            
            segments_with_paths.append(("\n", "", None)) # Add a newline between terms

        # --- Overall Summary Footer ---
        segments_with_paths.append(("--- Overall Batch Statistics ---\n", "category_header", None))
        segments_with_paths.append((f"Total terms processed: {total_terms_processed}\n", "item_detail", None))
        segments_with_paths.append((f"Terms with results: {terms_with_results}\n", "item_detail", None))
        segments_with_paths.append((f"Total files found across all terms: {total_files_found}\n", "item_detail", None))

        return segments_with_paths
