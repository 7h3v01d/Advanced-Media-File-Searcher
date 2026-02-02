import os
import threading
import time
import re # Only if BaseParser methods were directly moved here, but they are expected in FileSearchService.


class BatchProcessor:
    """
    Handles the core logic for batch processing search terms.
    It orchestrates calls to the FileSearchService and manages batch-specific
    features like "Single" or "Multiple" instance finding.
    """
    def __init__(self, file_search_service):
        """
        Initializes the BatchProcessor.

        Args:
            file_search_service (FileSearchService): An instance of the FileSearchService
                                                     to perform individual search operations.
        """
        self.file_search_service = file_search_service
        self.batch_process_running = threading.Event() # Flag to signal if batch process should continue
        self.current_batch_thread = None # Reference to the active batch processing thread

    def start_batch_processing(self, search_terms, batch_location, selected_type,
                               exact_match, instance_mode,
                               progress_callback, error_callback, completion_callback):
        """
        Starts the batch processing in a new thread.

        Args:
            search_terms (list): A list of search terms (strings) loaded from the batch file.
            batch_location (str): The directory path where searches should be performed.
            selected_type (str): The content type filter (e.g., "Movie", "TV Show", "All").
            exact_match (bool): True for exact filename matching, False for smart matching.
            instance_mode (str): "Single" to find only the first match per term, "Multiple" for all matches.
            progress_callback (callable): A function (or lambda) to call with progress messages.
                                          This callback should be safe for GUI updates (e.g., scheduled via `master.after`).
                                          Signature: `progress_callback(message: str)`
            error_callback (callable): A function (or lambda) to call if an error occurs during a single search.
                                       Signature: `error_callback(message: str)`
            completion_callback (callable): A function (or lambda) to call when the entire batch process finishes.
                                            Signature: `completion_callback(all_results: list, was_stopped: bool)`
        """
        if self.current_batch_thread and self.current_batch_thread.is_alive():
            error_callback("Batch process is already running.")
            return

        self.batch_process_running.set() # Set the flag to indicate the process should run
        
        # Create and start a new thread for the batch processing
        self.current_batch_thread = threading.Thread(target=self._execute_batch_job, args=(
            search_terms, batch_location, selected_type, exact_match, instance_mode,
            progress_callback, error_callback, completion_callback
        ))
        self.current_batch_thread.start()
        print("INFO: BatchProcessor: Batch processing thread started.")

    def stop_batch_processing(self):
        """
        Signals the running batch process to stop gracefully.
        The `_execute_batch_job` loop will check this flag and exit.
        """
        self.batch_process_running.clear()
        print("INFO: BatchProcessor: Stop signal sent to batch thread.")
        # Optionally, wait for the thread to actually finish if immediate shutdown is critical
        # if self.current_batch_thread and self.current_batch_thread.is_alive():
        #     self.current_batch_thread.join(timeout=5) # Wait up to 5 seconds for it to finish
        #     if self.current_batch_thread.is_alive():
        #         print("WARNING: BatchProcessor: Batch thread did not terminate gracefully within timeout.")

    def _execute_batch_job(self, search_terms, batch_location, selected_type,
                           exact_match, instance_mode,
                           progress_callback, error_callback, completion_callback):
        """
        The main loop for batch processing. This method runs in a separate thread.
        It iterates through each search term, calls the FileSearchService, and collects results.
        """
        all_batch_results = [] # Stores results for all terms in the batch
        num_terms = len(search_terms)

        for i, term in enumerate(search_terms):
            # Check if the stop signal has been received before processing the next term
            if not self.batch_process_running.is_set():
                # If stopped, call the main completion callback with a flag indicating it was stopped
                print(f"INFO: BatchProcessor: Batch process stopped by user after {i} terms.")
                completion_callback(all_batch_results, True) # True for was_stopped
                return # Exit the thread immediately

            # Update GUI with current term progress
            progress_callback(f"Searching for term {i+1}/{num_terms}: '{term}'")
            
            # Event to signal completion of an individual search within the batch loop
            single_search_complete_event = threading.Event()
            current_term_search_results = [] # To store results from the FileSearchService for THIS term
            current_term_error = None # To store any error message for THIS term

            # Define inner callbacks that interact with the local scope and outer callbacks
            def result_cb_inner(results, s_term_inner, s_type_inner):
                """Callback for FileSearchService to append results."""
                nonlocal current_term_search_results
                current_term_search_results.extend(results)

            def error_cb_inner(msg):
                """Callback for FileSearchService to report errors."""
                nonlocal current_term_error
                current_term_error = msg
                print(f"ERROR: BatchProcessor (Internal): FileSearchService error for term '{term}': {msg}")

            def completion_cb_inner():
                """Callback for FileSearchService to signal completion of a single search."""
                single_search_complete_event.set() # Release the wait for this specific search

            # Initiate the actual search using the FileSearchService instance
            self.file_search_service.start_search(
                search_term=term,
                search_location=batch_location,
                selected_type=selected_type,
                exact_match_mode=exact_match,
                result_callback=result_cb_inner,
                error_callback=error_cb_inner,
                completion_callback=completion_cb_inner
            )

            # Wait for the individual search for the current term to complete
            # A reasonable timeout is crucial to prevent the batch process from hanging
            single_search_complete_event.wait(timeout=3600) # Max wait of 1 hour per search

            # Process the results for the current term based on instance_mode
            final_results_for_term = []
            if current_term_error:
                # If an error occurred during the search for this term
                all_batch_results.append({
                    'term': term,
                    'results': [], # No results due to error
                    'filter_type': selected_type,
                    'exact_match': exact_match,
                    'status': 'error',
                    'error_message': current_term_error
                })
            elif current_term_search_results:
                # If results were found for this term
                if instance_mode == "Single":
                    # If "Single" mode, take only the first result found
                    final_results_for_term = [current_term_search_results[0]]
                else: # "Multiple" mode, take all results
                    final_results_for_term = current_term_search_results
                
                all_batch_results.append({
                    'term': term,
                    'results': final_results_for_term,
                    'filter_type': selected_type,
                    'exact_match': exact_match,
                    'status': 'completed'
                })
            else:
                # No results found for this term
                all_batch_results.append({
                    'term': term,
                    'results': [],
                    'filter_type': selected_type,
                    'exact_match': exact_match,
                    'status': 'no_results'
                })
            
            # Short pause to allow GUI updates and prevent 100% CPU usage
            time.sleep(0.1)

        # After processing all terms (or if stopped gracefully)
        print("INFO: BatchProcessor: All terms processed or batch completed.")
        completion_callback(all_batch_results, False) # False for was_stopped (means it completed naturally)
