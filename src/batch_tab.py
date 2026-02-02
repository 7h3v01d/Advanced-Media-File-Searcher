import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import subprocess
import threading
import time
import re 

# Import from new utility file
from gui_utilities import TextRedirector, format_bytes
# Import the new BatchProcessor
from batch_processor import BatchProcessor

class BatchTabFrame(tk.Frame):
    def __init__(self, parent_notebook, master_app_instance, search_service, text_redirector, debug_info_var, dark_mode_var):
        """
        Initializes the BatchTabFrame.

        Args:
            parent_notebook (ttk.Notebook): The notebook widget this tab will be added to.
            master_app_instance (FileSearchGUI): Reference to the main GUI application instance.
            search_service (FileSearchService): The service responsible for performing file searches (will be used by batch later).
            text_redirector (TextRedirector): The custom stdout redirector for GUI logging.
            debug_info_var (tk.BooleanVar): A BooleanVar controlling debug output visibility.
            dark_mode_var (tk.BooleanVar): A BooleanVar controlling dark mode state.
        """
        super().__init__(parent_notebook)
        self.master_app = master_app_instance # Store reference to main app
        self.search_service = search_service # Keep reference to the service, even if not fully used yet
        self.text_redirector = text_redirector
        self.debug_info_var = debug_info_var
        self.dark_mode_var = dark_mode_var

        # Initialize the BatchProcessor with the existing search_service
        self.batch_processor = BatchProcessor(self.search_service)

        self.batch_search_terms = [] # List to store terms from the batch file
        # self.batch_process_running = threading.Event() # This flag is now managed by BatchProcessor

        # Configure grid for this frame (increased number of rows)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        # Now 14 rows are configured (0-13) to accommodate new widgets
        for i in range(14): 
            self.grid_rowconfigure(i, weight=0)
        self.grid_rowconfigure(11, weight=1) # Output text area row (now at index 11) gets weight


        # --- Widgets for Batch Tab ---

        # 1. Batch Input File/Folder (Row 0, 1)
        self.batch_input_label = tk.Label(self, text="Select Batch Input (File or Folder/TXT File):")
        self.batch_input_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        self.batch_input_entry = tk.Entry(self, width=60)
        self.batch_input_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        self.batch_input_entry.insert(0, os.path.expanduser("~") if os.name == 'posix' else os.getcwd())

        self.browse_batch_input_button = tk.Button(self, text="Browse Input", command=self.select_batch_file,
                                              relief="raised", bd=2, padx=10, pady=5)
        self.browse_batch_input_button.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 5), columnspan=2)

        # 2. Output Location Input (Row 2, 3)
        self.output_location_label = tk.Label(self, text="Select Output Folder (Optional):")
        self.output_location_label.grid(row=2, column=0, sticky="w", padx=10, pady=(10, 0))

        self.output_location_entry = tk.Entry(self, width=60)
        self.output_location_entry.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))
        self.output_location_entry.insert(0, os.path.expanduser("~") if os.name == 'posix' else os.getcwd())

        self.browse_output_folder_button = tk.Button(self, text="Browse Output", command=self.browse_output_folder,
                                                    relief="raised", bd=2, padx=10, pady=5)
        self.browse_output_folder_button.grid(row=3, column=1, sticky="ew", padx=10, pady=(0, 5), columnspan=2)

        # 3. Folder to Search (New: Row 4, 5)
        self.location_label_batch = tk.Label(self, text="Folder to Search:")
        self.location_label_batch.grid(row=4, column=0, sticky="w", padx=10, pady=(10, 0))

        self.location_entry_batch = tk.Entry(self, width=60)
        self.location_entry_batch.grid(row=5, column=0, sticky="ew", padx=10, pady=(0, 5))
        self.location_entry_batch.insert(0, os.path.expanduser("~") if os.name == 'posix' else os.getcwd())

        self.browse_location_button_batch = tk.Button(self, text="Browse Folder", command=self._browse_batch_location,
                                                       relief="raised", bd=2, padx=10, pady=5)
        self.browse_location_button_batch.grid(row=5, column=1, sticky="ew", padx=10, pady=(0, 5), columnspan=2)


        # 4. Batch Instance Options (New: Replaces old Batch Options at Row 6)
        self.batch_instance_label = tk.Label(self, text="Find Instances:")
        self.batch_instance_label.grid(row=6, column=0, sticky="w", padx=10, pady=(10, 0))

        self.batch_instance_var = tk.StringVar(value="Multiple") # Default to Multiple
        self.batch_instance_frame = tk.Frame(self)
        self.batch_instance_frame.grid(row=6, column=0, columnspan=3, sticky="ew", padx=(100, 10), pady=(10, 5))
        self.radio_single_instance = tk.Radiobutton(self.batch_instance_frame, text="Single", variable=self.batch_instance_var, value="Single")
        self.radio_single_instance.pack(side="left", padx=5)
        self.radio_multiple_instance = tk.Radiobutton(self.batch_instance_frame, text="Multiple", variable=self.batch_instance_var, value="Multiple")
        self.radio_multiple_instance.pack(side="left", padx=5)


        # 5. Filter by Content Type (Radio Buttons) (Now at Row 7)
        self.filter_type_label = tk.Label(self, text="Filter by Content Type:")
        self.filter_type_label.grid(row=7, column=0, sticky="w", padx=10, pady=(10, 0))

        self.filter_radio_frame = tk.Frame(self)
        self.filter_radio_frame.grid(row=7, column=0, columnspan=3, sticky="ew", padx=(140, 10), pady=(10, 5))

        self.search_type_var = tk.StringVar(value="TV Show") # Renamed from batch_search_type_var for consistency
        self.radio_movie_batch = tk.Radiobutton(self.filter_radio_frame, text="Movie", variable=self.search_type_var, value="Movie")
        self.radio_movie_batch.pack(side="left", padx=5)
        self.radio_tv_show_batch = tk.Radiobutton(self.filter_radio_frame, text="TV Show", variable=self.search_type_var, value="TV Show")
        self.radio_tv_show_batch.pack(side="left", padx=5)
        self.radio_other_batch = tk.Radiobutton(self.filter_radio_frame, text="Other", variable=self.search_type_var, value="Other")
        self.radio_other_batch.pack(side="left", padx=5)
        self.radio_all_batch = tk.Radiobutton(self.filter_radio_frame, text="All Categories", variable=self.search_type_var, value="All")
        self.radio_all_batch.pack(side="left", padx=5)


        # 6. Checkbox Options (Now at Row 8)
        self.checkbox_frame_batch = tk.Frame(self) # Unique name for this tab's checkbox frame
        self.checkbox_frame_batch.grid(row=8, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 5))

        # Dark Mode Checkbox
        self.dark_mode_checkbox_batch = tk.Checkbutton(self.checkbox_frame_batch, text="Dark Mode", variable=self.dark_mode_var,
                                  command=self.master_app.toggle_dark_mode) # Call main app's toggle method
        self.dark_mode_checkbox_batch.pack(side="left", padx=5)

        # Debug Info Checkbox
        self.debug_info_checkbox_batch = tk.Checkbutton(self.checkbox_frame_batch, text="Show Debug Info", variable=self.debug_info_var)
        self.debug_info_checkbox_batch.pack(side="left", padx=15)

        # Exact Match Checkbox
        self.exact_match_var_batch = tk.BooleanVar(value=False) # Unique name for this tab's exact match var
        self.exact_match_checkbox_batch = tk.Checkbutton(self.checkbox_frame_batch, text="Exact Match", variable=self.exact_match_var_batch)
        self.exact_match_checkbox_batch.pack(side="left", padx=15)


        # 7. Batch Action Buttons (Start/Stop) (Now at Row 9)
        self.batch_button_row_frame = tk.Frame(self)
        self.batch_button_row_frame.grid(row=9, column=0, columnspan=3, pady=15, padx=10, sticky="ew")
        self.batch_button_row_frame.grid_columnconfigure(0, weight=1)
        self.batch_button_row_frame.grid_columnconfigure(1, weight=1)

        self.start_batch_button = tk.Button(self.batch_button_row_frame, text="Start Batch Process", command=self.start_batch_process,
                                            relief="raised", bd=2, padx=20, pady=10, font=("TkDefaultFont", 10, "bold"))
        self.start_batch_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.stop_batch_button = tk.Button(self.batch_button_row_frame, text="Stop Batch Process", command=self.stop_batch_process,
                                           relief="raised", bd=2, padx=20, pady=10, font=("TkDefaultFont", 10, "bold"),
                                           state=tk.DISABLED) # Initially disabled
        self.stop_batch_button.grid(row=0, column=1, padx=5, sticky="ew")


        # 8. Output Area Header (Label + Clear Buttons) (Now at Row 10)
        self.output_header_frame = tk.Frame(self)
        self.output_header_frame.grid(row=10, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 0))
        self.output_header_frame.grid_columnconfigure(0, weight=1)
        self.output_header_frame.grid_columnconfigure(1, weight=0)
        self.output_header_frame.grid_columnconfigure(2, weight=0)

        self.output_label = tk.Label(self.output_header_frame, text="Batch Output:")
        self.output_label.grid(row=0, column=0, sticky="w")

        self.clear_output_button = tk.Button(self.output_header_frame, text="Clear Output", command=self.clear_output_only,
                                            relief="raised", bd=2, padx=5, pady=2, font=("TkDefaultFont", 9))
        self.clear_output_button.grid(row=0, column=1, padx=(5, 5), sticky="e")

        self.clear_all_button = tk.Button(self.output_header_frame, text="Clear All", command=self.clear_all_fields_and_output,
                                       relief="raised", bd=2, padx=5, pady=2, font=("TkDefaultFont", 9))
        self.clear_all_button.grid(row=0, column=2, padx=(5, 0), sticky="e")


        # 9. Actual Output Text Area (Now at Row 11)
        self.output_text = tk.Text(self, wrap="word", height=30, width=120, relief="sunken", bd=1)
        self.output_text.grid(row=11, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))

        self.output_scrollbar = tk.Scrollbar(self, command=self.output_text.yview)
        self.output_scrollbar.grid(row=11, column=2, sticky="ns", pady=(0, 10))
        self.output_text['yscrollcommand'] = self.output_scrollbar.set

        # Context Menu for results (can be generic for file paths)
        self.context_menu = tk.Menu(self, tearoff=0)
        self.output_text.bind("<Button-3>", self._show_context_menu)

        # Set the output text widget for the redirector
        self.text_redirector.set_output_text_widget(self.output_text)

    def apply_theme(self, theme, ttk_style):
        """Applies the current theme colors to all widgets within this tab."""
        self.config(bg=theme["bg"])

        for label in [self.batch_input_label, self.output_location_label, self.location_label_batch,
                      self.batch_instance_label, # Updated label reference
                      self.filter_type_label, self.output_label]:
            label.config(bg=theme["bg"], fg=theme["label_fg"])

        self.batch_input_entry.config(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"])
        self.output_location_entry.config(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"])
        self.location_entry_batch.config(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"])

        button_fg_color = theme["button_fg"]
        self.browse_batch_input_button.config(bg=theme["button_bg"], fg=button_fg_color, activebackground=theme["button_bg"])
        self.browse_output_folder_button.config(bg=theme["button_bg"], fg=button_fg_color, activebackground=theme["button_bg"])
        self.browse_location_button_batch.config(bg=theme["button_bg"], fg=button_fg_color, activebackground=theme["button_bg"])
        self.start_batch_button.config(bg=theme["start_button_bg"], fg=button_fg_color, activebackground=theme["start_button_bg"])
        self.stop_batch_button.config(bg=theme["stop_button_bg"], fg=button_fg_color, activebackground=theme["stop_button_bg"])
        self.clear_output_button.config(bg=theme["clear_button_bg"], fg=button_fg_color, activebackground=theme["clear_button_bg"])
        self.clear_all_button.config(bg=theme["clear_button_bg"], fg=button_fg_color, activebackground=theme["clear_button_bg"])

        # New: Theme for Batch Instance radios
        self.batch_instance_frame.config(bg=theme["bg"])
        for radio in [self.radio_single_instance, self.radio_multiple_instance]:
            radio.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])

        # Theme for Filter by Content Type radios
        self.filter_radio_frame.config(bg=theme["bg"])
        for radio in [self.radio_movie_batch, self.radio_tv_show_batch, self.radio_other_batch, self.radio_all_batch]:
            radio.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])

        # Theme for Checkboxes
        self.checkbox_frame_batch.config(bg=theme["bg"])
        self.dark_mode_checkbox_batch.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])
        self.debug_info_checkbox_batch.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])
        self.exact_match_checkbox_batch.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])

        self.output_text.config(bg=theme["output_bg"], fg=theme["output_fg"])

        # Apply colors to specific output text tags (assuming they exist in the main app's theme)
        self.output_text.tag_config("error", foreground=theme["error_fg"])
        self.output_text.tag_config("info", foreground=theme["info_fg"])
        self.output_text.tag_config("debug", foreground=theme["debug_fg"])
        self.output_text.tag_config("warning", foreground=theme["warning_fg"])
        self.output_text.tag_config("summary_not_found", foreground=theme["summary_not_found_fg"])
        self.output_text.tag_config("summary_found", foreground=theme["summary_found_fg"])
        self.output_text.tag_config("category_header", foreground=theme["category_header_fg"])
        self.output_text.tag_config("item_detail", foreground=theme["item_detail_fg"])
        self.output_text.tag_config("item_detail_parsed", foreground=theme["item_detail_parsed_fg"])
        
        # ttk Combobox styling (if any are added to this tab)
        ttk_style.configure("TCombobox",
                             fieldbackground=theme["entry_bg"],
                             background=theme["button_bg"],
                             foreground=theme["entry_fg"],
                             selectbackground=theme["entry_bg"],
                             selectforeground=theme["entry_fg"],
                             bordercolor=theme["notebook_bg"],
                             arrowcolor=theme["entry_fg"])
        ttk_style.map("TCombobox",
                       fieldbackground=[("readonly", theme["entry_bg"])],
                       background=[("readonly", theme["button_bg"])],
                       foreground=[("readonly", theme["entry_fg"])])


    def select_batch_file(self):
        """Allows the user to select a text file for batch input."""
        filepath = filedialog.askopenfilename(parent=self.master_app.master,
                                             initialdir=self.batch_input_entry.get() or os.getcwd(),
                                             title="Select Batch Input Text File",
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filepath:
            self.batch_input_entry.delete(0, tk.END)
            self.batch_input_entry.insert(0, filepath)
            self.batch_search_terms = []
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        stripped_line = line.strip()
                        if stripped_line: # Only add non-empty lines
                            self.batch_search_terms.append(stripped_line)
                print(f"INFO: Loaded {len(self.batch_search_terms)} terms from batch file: {filepath}")
                self.clear_output_only()
                self.output_text.insert(tk.END, f"Loaded {len(self.batch_search_terms)} search terms from '{os.path.basename(filepath)}'.\nReady to start batch process.\n", "info")
            except Exception as e:
                messagebox.showerror("File Read Error", f"Failed to read batch file: {e}")
                print(f"ERROR: Failed to read batch file {filepath}: {e}")
                self.batch_search_terms = [] # Clear terms on error
        else:
            print("INFO: Batch file selection cancelled.")
            self.batch_search_terms = [] # Clear terms if selection cancelled


    def start_batch_process(self):
        """Starts the batch processing in a separate thread."""
        if not self.batch_search_terms:
            messagebox.showwarning("Batch Input Missing", "Please load a batch text file with search terms first.")
            print("WARNING: Batch process not started: No terms loaded.")
            return

        batch_location = self.location_entry_batch.get().strip()
        if not os.path.isdir(batch_location):
            messagebox.showerror("Invalid Folder", "Batch Search Folder does not exist or is not a valid directory.")
            print(f"ERROR: Invalid batch search folder: {batch_location}")
            return

        self.master_app.show_overlay()
        self.text_redirector.flush()
        self.output_text.delete(1.0, tk.END)
        print("INFO: Initiating real batch process...")
        
        self.start_batch_button.config(state=tk.DISABLED)
        self.stop_batch_button.config(state=tk.NORMAL)
        
        # Call the BatchProcessor to start processing
        self.batch_processor.start_batch_processing(
            search_terms=self.batch_search_terms,
            batch_location=batch_location,
            selected_type=self.search_type_var.get(),
            exact_match=self.exact_match_var_batch.get(),
            instance_mode=self.batch_instance_var.get(),
            # Callbacks need to be wrapped to be executed on the main Tkinter thread
            progress_callback=lambda msg: self.master_app.master.after(0, self._update_batch_progress_display, msg),
            error_callback=lambda msg: self.master_app.master.after(0, messagebox.showerror, "Batch Process Error", msg),
            completion_callback=lambda results, was_stopped: self.master_app.master.after(0, self._finalize_batch_display, results, was_stopped)
        )


    def _update_batch_progress_display(self, message):
        """Updates the output text area with progress messages."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, f"INFO: {message}\n", "info")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def _finalize_batch_display(self, all_batch_results, was_stopped):
        """
        Displays the aggregated results of the batch process in the GUI's Text widget.
        Called on completion of the batch thread.
        Includes functionality to save the report to a file if an output folder is chosen.
        """
        self.output_text.config(state=tk.NORMAL) # Enable editing
        self.output_text.delete(1.0, tk.END) # Clear existing progress messages

        report_content = []
        
        # --- Overall Batch Summary Header ---
        if was_stopped:
            report_header = "--- Batch Process: STOPPED by User ---\n\n"
            report_content.append(report_header)
            self.output_text.insert(tk.END, report_header, "warning")
            print("INFO: Batch process was manually stopped.")
        else:
            report_header = "--- Batch Process Summary ---\n\n"
            report_content.append(report_header)
            self.output_text.insert(tk.END, report_header, "summary_found")
            print("INFO: Batch process completed.")

        total_files_found = 0
        total_terms_processed = len(all_batch_results)
        terms_with_results = 0

        # --- Details for Each Term ---
        for i, batch_item in enumerate(all_batch_results):
            term = batch_item['term']
            results_for_term = batch_item['results']
            filter_type = batch_item['filter_type']
            exact_match = batch_item['exact_match']
            status = batch_item['status']
            error_message = batch_item.get('error_message', '')

            # Add a separator and term details
            term_display = f"[{i+1}/{total_terms_processed}] Term: '{term}' (Filter: {filter_type}, Exact Match: {exact_match})\n"
            report_content.append(term_display)
            self.output_text.insert(tk.END, term_display, "category_header")

            if status == 'error':
                error_msg_line = f"  Status: ERROR - {error_message}\n"
                report_content.append(error_msg_line)
                self.output_text.insert(tk.END, error_msg_line, "error")
            elif status == 'completed' and results_for_term:
                found_msg = f"  Found {len(results_for_term)} items.\n"
                report_content.append(found_msg)
                self.output_text.insert(tk.END, found_msg, "summary_found")
                total_files_found += len(results_for_term)
                terms_with_results += 1
                
                for item in results_for_term:
                    # Adjusted indentation for "File:" to match user's desired output
                    file_info = f"      File: {os.path.basename(item['raw_path'])}\n"
                    path_info = f"        Path: {item['raw_path']}\n" # Further indent path
                    size_info = f"        Size: {format_bytes(item['size_bytes'])}\n"
                    category_info = f"        Category: {item['category']}\n"

                    report_content.extend([file_info, path_info, size_info, category_info])
                    self.output_text.insert(tk.END, file_info, "item_detail")
                    self.output_text.insert(tk.END, path_info, "item_detail")
                    self.output_text.insert(tk.END, size_info, "item_detail")
                    self.output_text.insert(tk.END, category_info, "item_detail")

                    # Display 'Parsed' data only if debug is enabled
                    if self.debug_info_var.get():
                        parsed_data = item.get("parsed_data", {})
                        if parsed_data: # Ensure there's actual parsed data
                            parsed_info_lines = []
                            for key, value in parsed_data.items():
                                parsed_info_lines.append(f"{key}='{value}'")
                            
                            parsed_line_content = ", ".join(parsed_info_lines)
                            if parsed_line_content:
                                parsed_line = f"        Parsed: {parsed_line_content}\n"
                                report_content.append(parsed_line)
                                self.output_text.insert(tk.END, parsed_line, "item_detail_parsed")
                        else:
                             parsed_line = f"        Parsed: No detailed parsing data available.\n"
                             report_content.append(parsed_line)
                             self.output_text.insert(tk.END, parsed_line, "item_detail_parsed")
            else: # No results found
                no_results_msg = "  No results found for this term.\n"
                report_content.append(no_results_msg)
                self.output_text.insert(tk.END, no_results_msg, "summary_not_found")
            
            report_content.append("\n") # Add a newline between terms in report
            self.output_text.insert(tk.END, "\n") # Add a newline between terms in display


        # --- Overall Summary Footer ---
        overall_summary_header = "--- Overall Batch Statistics ---\n"
        total_terms_processed_line = f"  Total terms processed: {total_terms_processed}\n"
        terms_with_results_line = f"  Terms with results: {terms_with_results}\n"
        total_files_found_line = f"  Total files found across all terms: {total_files_found}\n"

        report_content.extend([overall_summary_header, total_terms_processed_line,
                               terms_with_results_line, total_files_found_line])
        self.output_text.insert(tk.END, overall_summary_header, "category_header")
        self.output_text.insert(tk.END, total_terms_processed_line, "item_detail")
        self.output_text.insert(tk.END, terms_with_results_line, "item_detail")
        self.output_text.insert(tk.END, total_files_found_line, "item_detail")
        
        self.output_text.config(state=tk.DISABLED) # Disable editing

        # --- Save report to file if output folder is specified ---
        output_folder_path = self.output_location_entry.get().strip()
        if output_folder_path and os.path.isdir(output_folder_path):
            try:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                report_filename = f"batch_report_{timestamp}.txt"
                report_filepath = os.path.join(output_folder_path, report_filename)
                with open(report_filepath, 'w', encoding='utf-8') as f:
                    f.writelines(report_content)
                print(f"INFO: Batch report saved to: {report_filepath}")
                messagebox.showinfo("Report Saved", f"Batch report saved successfully to:\n{report_filepath}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save batch report:\n{e}")
                print(f"ERROR: Failed to save batch report to {output_folder_path}: {e}")
        elif output_folder_path: # Path was entered but not a directory
            messagebox.showwarning("Invalid Output Folder", "The specified output folder is not a valid directory. Report not saved.")
            print(f"WARNING: Output folder '{output_folder_path}' is not a valid directory. Report not saved.")
        else:
            print("INFO: No output folder specified. Batch report not saved to file.")


        self.master_app.hide_overlay()
        self.start_batch_button.config(state=tk.NORMAL)
        self.stop_batch_button.config(state=tk.DISABLED)
        self.text_redirector.flush() # Ensure all messages are flushed
        print("INFO: Batch process results displayed.")


    def stop_batch_process(self):
        """Signals the batch process to stop."""
        self.batch_processor.stop_batch_processing() # Now calls the BatchProcessor's stop method
        print("INFO: Batch process stop requested.")


    def _browse_batch_location(self):
        """Allows the user to select a directory for the batch search location."""
        selected_directory = filedialog.askdirectory(parent=self.master_app.master,
                                                     initialdir=self.location_entry_batch.get() or os.getcwd(),
                                                     title="Select Folder for Batch Search")
        if selected_directory:
            self.location_entry_batch.delete(0, tk.END)
            self.location_entry_batch.insert(0, selected_directory)
            print(f"INFO: Batch search folder selected: {selected_directory}")
        else:
            print("INFO: Batch search folder selection cancelled.")

    def browse_output_folder(self):
        """Allows the user to select an output directory for batch processing."""
        selected_directory = filedialog.askdirectory(parent=self.master_app.master,
                                                     initialdir=self.output_location_entry.get() or os.getcwd(),
                                                     title="Select Output Folder")
        if selected_directory:
            self.output_location_entry.delete(0, tk.END)
            self.output_location_entry.insert(0, selected_directory)
            print(f"INFO: Output folder selected: {selected_directory}")
        else:
            print("INFO: Output folder selection cancelled.")

    def clear_output_only(self):
        """Clears only the output text area."""
        self.text_redirector.flush()
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        print("INFO: Batch output area cleared.")

    def clear_all_fields_and_output(self):
        """Clears all input fields and the output text area in the batch tab, resetting the UI."""
        self.batch_input_entry.delete(0, tk.END)
        self.batch_input_entry.insert(0, os.path.expanduser("~") if os.name == 'posix' else os.getcwd())
        self.output_location_entry.delete(0, tk.END)
        self.output_location_entry.insert(0, os.path.expanduser("~") if os.name == 'posix' else os.getcwd())
        self.location_entry_batch.delete(0, tk.END) # Clear new location entry
        self.location_entry_batch.insert(0, os.path.expanduser("~") if os.name == 'posix' else os.getcwd()) # Reset new location entry
        self.batch_instance_var.set("Multiple") # Reset new instance radio button to default
        self.search_type_var.set("TV Show") # Reset filter type radio button
        self.exact_match_var_batch.set(False) # Uncheck exact match
        self.batch_search_terms = [] # Clear loaded terms
        self.clear_output_only()
        print("INFO: All batch fields and output cleared.")
        self.start_batch_button.config(state=tk.NORMAL)
        self.stop_batch_button.config(state=tk.DISABLED)

    def _get_filepath_at_cursor(self, event):
        """
        Attempts to extract a file path from the line under the mouse cursor in the output area.
        """
        try:
            index = self.output_text.index(f"@{event.x},{event.y}")
            line_start = self.output_text.index(index + " linestart")
            line_end = self.output_text.index(index + " lineend")
            line_content = self.output_text.get(line_start, line_end)

            # This is a generic path extraction; might need refinement based on actual batch output format
            if "Path: " in line_content: # More specific for search tab style output
                filepath = line_content.split("Path: ", 1)[1].strip()
            elif os.path.exists(line_content.strip()): # Check if the whole line is a path
                filepath = line_content.strip()
            else:
                return None
            
            if os.path.exists(filepath):
                return filepath
            return None
        except tk.TclError:
            return None

    def _show_context_menu(self, event):
        """
        Displays a context menu for file actions on the output text area.
        """
        self.context_menu.delete(0, tk.END)
        filepath = self._get_filepath_at_cursor(event)

        if filepath and os.path.exists(filepath):
            self.context_menu.add_command(label="Open File Location", command=lambda: self._open_file_location(filepath))
            self.context_menu.add_command(label="Copy File Path", command=lambda: self._copy_filepath(filepath))
            self.context_menu.add_command(label="Open File", command=lambda: self._open_file(filepath))
        else:
            self.context_menu.add_command(label="No file path found", state=tk.DISABLED)
            
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _open_file_location(self, filepath):
        """Opens the folder containing the given file in the OS file explorer."""
        folder_path = os.path.dirname(filepath)
        if not os.path.isdir(folder_path):
            messagebox.showerror("Error", f"Folder not found: {folder_path}")
            print(f"ERROR: Folder not found for opening: {folder_path}")
            return

        try:
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin": # macOS
                subprocess.run(["open", folder_path])
            else: # Linux and other POSIX-like systems
                subprocess.run(["xdg-open", folder_path])
            print(f"INFO: Opened folder: {folder_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")
            print(f"ERROR: Failed to open folder {folder_path}: {e}")

    def _copy_filepath(self, filepath):
        """Copies the given file path to the clipboard."""
        try:
            self.master_app.master.clipboard_clear()
            self.master_app.master.clipboard_append(filepath)
            messagebox.showinfo("Copied", "File path copied to clipboard.")
            print(f"INFO: Copied to clipboard: {filepath}")
        except tk.TclError as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
            print(f"ERROR: Failed to copy {filepath} to clipboard: {e}")

    def _open_file(self, filepath):
        """Opens the given file with its default application."""
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File not found: {filepath}")
            print(f"ERROR: File not found for opening: {filepath}")
            return
        
        try:
            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin": # macOS
                subprocess.run(["open", filepath])
            else: # Linux and other POSIX-like systems
                subprocess.run(["xdg-open", filepath])
            print(f"INFO: Opened file: {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")
            print(f"ERROR: Failed to open file {filepath}: {e}")

