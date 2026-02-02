import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import subprocess
import threading
import time
import re
import uuid # Import uuid for unique tags

# Import from new utility file
from gui_utilities import TextRedirector, format_bytes
# Import the new BatchProcessor
from batch_processor import BatchProcessor
from output_formatter import OutputFormatter # Import the OutputFormatter

class BatchTabFrame(tk.Frame):
    def __init__(self, parent_notebook, master_app_instance, search_service, text_redirector, debug_info_var, dark_mode_var, default_search_location):
        """
        Initializes the BatchTabFrame.

        Args:
            parent_notebook (ttk.Notebook): The notebook widget this tab will be added to.
            master_app_instance (FileSearchGUI): Reference to the main GUI application instance.
            search_service (FileSearchService): The service responsible for performing file searches (will be used by batch later).
            text_redirector (TextRedirector): The custom stdout redirector for GUI logging.
            debug_info_var (tk.BooleanVar): A BooleanVar controlling debug output visibility.
            dark_mode_var (tk.BooleanVar): A BooleanVar controlling dark mode state.
            default_search_location (str): The default folder path to use for searches.
        """
        super().__init__(parent_notebook)
        self.master_app = master_app_instance # Store reference to main app
        self.search_service = search_service # Keep reference to the service, even if not fully used yet
        self.text_redirector = text_redirector
        self.debug_info_var = debug_info_var
        self.dark_mode_var = dark_mode_var
        self.default_search_location = default_search_location # Store the passed default location

        self.batch_processor = BatchProcessor(self.search_service) # Initialize BatchProcessor

        self.last_batch_results = [] # To store results for sorting/exporting

        # Configure grid for this frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        for i in range(15): # Enough rows for widgets
            self.grid_rowconfigure(i, weight=0)
        self.grid_rowconfigure(12, weight=1) # Output text area row gets weight


        # --- Widgets ---

        # 1. Input File Selection
        self.input_file_label = tk.Label(self, text="Batch Search Terms (Text File - One per Line):")
        self.input_file_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        self.input_file_entry = tk.Entry(self, width=60)
        self.input_file_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))

        self.browse_input_button = tk.Button(self, text="Browse Input File", command=self.browse_input_file,
                                             relief="raised", bd=2, padx=10, pady=5)
        self.browse_input_button.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 5))

        # 2. Folder to Search (Re-added)
        self.search_location_label = tk.Label(self, text="Folder to Search:")
        self.search_location_label.grid(row=2, column=0, sticky="w", padx=10, pady=(10, 0))

        self.search_location_entry = tk.Entry(self, width=60)
        self.search_location_entry.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))
        # Set default value for search location from passed argument
        self.search_location_entry.insert(0, self.default_search_location)

        self.browse_search_location_button = tk.Button(self, text="Browse Folder", command=self.browse_search_location,
                                                       relief="raised", bd=2, padx=10, pady=5)
        self.browse_search_location_button.grid(row=3, column=1, sticky="ew", padx=10, pady=(0, 5))


        # 3. Output Folder Selection (Made optional)
        self.output_folder_label = tk.Label(self, text="Batch Report Output Folder (optional):")
        self.output_folder_label.grid(row=4, column=0, sticky="w", padx=10, pady=(10, 0))

        self.output_folder_entry = tk.Entry(self, width=60)
        self.output_folder_entry.grid(row=5, column=0, sticky="ew", padx=10, pady=(0, 5))

        self.browse_output_button = tk.Button(self, text="Browse Output Folder", command=self.browse_output_folder,
                                              relief="raised", bd=2, padx=10, pady=5)
        self.browse_output_button.grid(row=5, column=1, sticky="ew", padx=10, pady=(0, 5))
        
        # 4. Search Type Selection (Radio Buttons)
        self.search_type_label = tk.Label(self, text="Filter by Content Type:")
        self.search_type_label.grid(row=6, column=0, sticky="w", padx=10, pady=(10, 0))

        self.radio_frame = tk.Frame(self)
        self.radio_frame.grid(row=6, column=0, columnspan=3, sticky="ew", padx=(140, 10), pady=(10, 5))

        self.search_type_var = tk.StringVar(value="TV Show") # Default for batch
        self.radio_movie = tk.Radiobutton(self.radio_frame, text="Movie", variable=self.search_type_var, value="Movie")
        self.radio_movie.pack(side="left", padx=5)
        self.radio_tv_show = tk.Radiobutton(self.radio_frame, text="TV Show", variable=self.search_type_var, value="TV Show")
        self.radio_tv_show.pack(side="left", padx=5)
        self.radio_other = tk.Radiobutton(self.radio_frame, text="Other", variable=self.search_type_var, value="Other")
        self.radio_other.pack(side="left", padx=5)
        self.radio_all = tk.Radiobutton(self.radio_frame, text="All Categories", variable=self.search_type_var, value="All")
        self.radio_all.pack(side="left", padx=5)

        # 5. Checkbox Options
        self.checkbox_frame = tk.Frame(self)
        self.checkbox_frame.grid(row=7, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 5))

        # Exact Match Checkbox for Batch
        self.exact_match_var = tk.BooleanVar(value=False) # Default to False (smart search)
        self.exact_match_checkbox = tk.Checkbutton(self.checkbox_frame, text="Exact Match", variable=self.exact_match_var)
        self.exact_match_checkbox.pack(side="left", padx=5)

        # New: Find only one instance per term checkbox
        self.single_instance_var = tk.BooleanVar(value=True) # Default to True (find only one)
        self.single_instance_checkbox = tk.Checkbutton(self.checkbox_frame, text="Find Single Instance Per Term", variable=self.single_instance_var)
        self.single_instance_checkbox.pack(side="left", padx=15)


        # 6. Result Sorting
        self.sort_frame = tk.Frame(self)
        self.sort_frame.grid(row=8, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 5))

        self.sort_label = tk.Label(self.sort_frame, text="Sort Results By:")
        self.sort_label.pack(side="left", padx=(0, 5))

        self.sort_combobox = ttk.Combobox(self.sort_frame, textvariable=tk.StringVar(value="Filename (Ascending)"),
                                          values=[
                                            "Filename (Ascending)", "Filename (Descending)",
                                            "Size (Ascending)", "Size (Descending)",
                                            "Category (Ascending)", "Category (Descending)"
                                          ],
                                          state="readonly", width=25)
        self.sort_combobox.pack(side="left", padx=5)
        self.sort_combobox.set("Filename (Ascending)") # Set default value


        # 7. Batch Action Buttons
        self.button_row_frame = tk.Frame(self)
        self.button_row_frame.grid(row=9, column=0, columnspan=3, pady=15, padx=10, sticky="ew")
        self.button_row_frame.grid_columnconfigure(0, weight=1)
        self.button_row_frame.grid_columnconfigure(1, weight=1)

        self.start_batch_button = tk.Button(self.button_row_frame, text="Start Batch Process", command=self.start_batch_process,
                                            relief="raised", bd=2, padx=20, pady=10, font=("TkDefaultFont", 10, "bold"))
        self.start_batch_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.stop_batch_button = tk.Button(self.button_row_frame, text="Stop Batch Process", command=self.stop_batch_process,
                                           relief="raised", bd=2, padx=20, pady=10, font=("TkDefaultFont", 10, "bold"),
                                           state=tk.DISABLED) # Initially disabled
        self.stop_batch_button.grid(row=0, column=1, padx=5, sticky="ew")

        # 8. Export and Clear Buttons (for batch output)
        self.export_clear_frame = tk.Frame(self)
        self.export_clear_frame.grid(row=10, column=0, columnspan=3, sticky="ew", padx=10, pady=(5, 5))
        # Configure columns for right alignment: column 0 takes all extra space
        self.export_clear_frame.grid_columnconfigure(0, weight=1)
        self.export_clear_frame.grid_columnconfigure(1, weight=0) # For Export Report
        self.export_clear_frame.grid_columnconfigure(2, weight=0) # For Clear Batch Output


        self.export_report_button = tk.Button(self.export_clear_frame, text="Export Report", command=self.export_batch_report,
                                               relief="raised", bd=2, padx=5, pady=2, font=("TkDefaultFont", 9))
        self.export_report_button.grid(row=0, column=1, padx=(5, 5), sticky="e") # Placed in col 1, right-aligned

        self.clear_batch_output_button = tk.Button(self.export_clear_frame, text="Clear Batch Output", command=self.clear_batch_output,
                                                    relief="raised", bd=2, padx=5, pady=2, font=("TkDefaultFont", 9))
        self.clear_batch_output_button.grid(row=0, column=2, padx=(5, 0), sticky="e") # Placed in col 2, right-aligned


        # 9. Batch Output Text Area
        self.output_label = tk.Label(self, text="Batch Process Output:")
        self.output_label.grid(row=11, column=0, sticky="w", padx=10, pady=(10, 0))

        # Set a default monospace font here for better control over spacing and rendering
        self.output_text = tk.Text(self, wrap="word", height=20, width=120, relief="sunken", bd=1)
        self.output_text.grid(row=12, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))

        self.output_scrollbar = tk.Scrollbar(self, command=self.output_text.yview)
        self.output_scrollbar.grid(row=12, column=2, sticky="ns", pady=(0, 10))
        self.output_text['yscrollcommand'] = self.output_scrollbar.set

        # Bind right-click event to the output text area
        self.output_text.bind("<Button-3>", self._show_context_menu)
        self.path_tag_map = {} # Map to store path for context menu clicks

        # Set the output text widget for the redirector
        self.text_redirector.set_output_text_widget(self.output_text)


    def apply_theme(self, theme, ttk_style):
        """Applies the current theme colors to all widgets within this tab."""
        self.config(bg=theme["bg"])

        # Labels
        # Check if label widgets exist before configuring
        for label in [self.input_file_label, self.search_location_label, self.output_folder_label,
                       self.search_type_label, self.sort_label, self.output_label]:
            if label and label.winfo_exists():
                label.config(bg=theme["bg"], fg=theme["label_fg"])

        # Entries
        if self.input_file_entry and self.input_file_entry.winfo_exists():
            self.input_file_entry.config(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"])
        if self.search_location_entry and self.search_location_entry.winfo_exists():
            self.search_location_entry.config(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"])
        if self.output_folder_entry and self.output_folder_entry.winfo_exists():
            self.output_folder_entry.config(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"])

        # Determine button foreground color based on theme
        button_fg_color = theme["button_fg"]

        # Buttons
        # Check if button widgets exist before configuring
        for button in [self.browse_input_button, self.browse_search_location_button, self.browse_output_button,
                       self.start_batch_button, self.stop_batch_button,
                       self.export_report_button, self.clear_batch_output_button]:
            if button and button.winfo_exists():
                if button == self.start_batch_button:
                    button.config(bg=theme["start_button_bg"], fg=button_fg_color, activebackground=theme["start_button_bg"])
                elif button == self.stop_batch_button:
                    button.config(bg=theme["stop_button_bg"], fg=button_fg_color, activebackground=theme["stop_button_bg"])
                elif button == self.export_report_button or button == self.clear_batch_output_button:
                    button.config(bg=theme["clear_button_bg"], fg=button_fg_color, activebackground=theme["clear_button_bg"])
                else:
                    button.config(bg=theme["button_bg"], fg=button_fg_color, activebackground=theme["button_bg"])


        # Radio Buttons (they are inside a frame)
        if self.radio_frame and self.radio_frame.winfo_exists():
            self.radio_frame.config(bg=theme["bg"])
            for radio in [self.radio_movie, self.radio_tv_show, self.radio_other, self.radio_all]:
                if radio and radio.winfo_exists():
                    radio.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])

        # Checkboxes
        if self.checkbox_frame and self.checkbox_frame.winfo_exists():
            self.checkbox_frame.config(bg=theme["bg"])
            if self.exact_match_checkbox and self.exact_match_checkbox.winfo_exists():
                self.exact_match_checkbox.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])
            if self.single_instance_checkbox and self.single_instance_checkbox.winfo_exists():
                self.single_instance_checkbox.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])


        # Apply theme to other frames
        if self.button_row_frame and self.button_row_frame.winfo_exists():
            self.button_row_frame.config(bg=theme["bg"])
        if self.export_clear_frame and self.export_clear_frame.winfo_exists():
            self.export_clear_frame.config(bg=theme["bg"])
        if self.sort_frame and self.sort_frame.winfo_exists():
            self.sort_frame.config(bg=theme["bg"])

        # Output Text Area (general background/foreground)
        if self.output_text and self.output_text.winfo_exists():
            self.output_text.config(bg=theme["output_bg"], fg=theme["output_fg"])
            
            # Apply fonts to specific output text tags using a monospace font for alignment
            # Set a base font for general output text to ensure consistency
            self.output_text.config(font=("Courier New", 10)) # Base font for the Text widget

            self.output_text.tag_config("error", foreground=theme["error_fg"])
            self.output_text.tag_config("info", foreground=theme["info_fg"])
            self.output_text.tag_config("debug", foreground=theme["debug_fg"])
            self.output_text.tag_config("warning", foreground=theme["warning_fg"])
            self.output_text.tag_config("summary_not_found", foreground=theme["summary_not_found_fg"])
            self.output_text.tag_config("summary_found", foreground=theme["summary_found_fg"])
            self.output_text.tag_config("category_header", foreground=theme["category_header_fg"])
            
            # Explicitly set the font for item_detail and item_detail_parsed
            self.output_text.tag_config("item_detail", font=("Courier New", 10), foreground=theme["item_detail_fg"])
            self.output_text.tag_config("item_detail_parsed", font=("Courier New", 10), foreground=theme["item_detail_parsed_fg"])
            
            # New tag for the actual filename, bold and a different font but same size
            self.output_text.tag_config("item_filename_result", font=("Verdana", 10, "bold"), foreground=theme["item_detail_fg"])
            # Ensure header also uses Courier New for consistency if needed, adjust size as appropriate
            self.output_text.tag_config("summary_header_bold_large", font=("Courier New", 12, "bold"), foreground=theme["category_header_fg"])


        if self.sort_combobox and self.sort_combobox.winfo_exists():
            ttk_style.configure("TCombobox",
                                fieldbackground=theme["entry_bg"],
                                background=theme["button_bg"], # Dropdown button background
                                foreground=theme["entry_fg"],
                                selectbackground=theme["entry_bg"], # Background of selected item in dropdown list
                                selectforeground=theme["entry_fg"], # Foreground of selected item in dropdown list
                                bordercolor=theme["notebook_bg"],
                                arrowcolor=theme["entry_fg"])
            ttk_style.map("TCombobox",
                        fieldbackground=[("readonly", theme["entry_bg"])],
                        background=[("readonly", theme["button_bg"])],
                        foreground=[("readonly", theme["entry_fg"])])


    def start_batch_process(self):
        """Starts the batch processing in a separate thread."""
        self.master_app.show_overlay() # Show overlay from main app

        # Clear previous output
        self.clear_batch_output()
        self.path_tag_map = {} # Clear path map for new results

        input_filepath = self.input_file_entry.get().strip()
        batch_location = self.search_location_entry.get().strip() # Get the search location
        output_folder = self.output_folder_entry.get().strip()
        selected_type = self.search_type_var.get()
        exact_match_mode = self.exact_match_var.get()
        single_instance_mode = self.single_instance_var.get()
        
        if not input_filepath:
            messagebox.showerror("Input Error", "Please select an input file for batch processing.")
            self.master_app.hide_overlay()
            return
        if not os.path.exists(input_filepath):
            messagebox.showerror("Input Error", f"Input file not found: {input_filepath}")
            self.master_app.hide_overlay()
            return
        
        if not batch_location:
            messagebox.showerror("Input Error", "Please specify a folder to search for batch processing.")
            self.master_app.hide_overlay()
            return
        if not os.path.isdir(batch_location):
            messagebox.showerror("Input Error", f"Search location not found: {batch_location}")
            self.master_app.hide_overlay()
            return

        # Output folder is now optional
        if output_folder and not os.path.isdir(output_folder):
            messagebox.showerror("Input Error", "Invalid output folder. Please select a valid folder or leave blank.")
            self.master_app.hide_overlay()
            return

        # Read search terms from the input file
        try:
            with open(input_filepath, 'r', encoding='utf-8') as f:
                search_terms_list = [line.strip() for line in f if line.strip()]
        except Exception as e:
            messagebox.showerror("File Error", f"Failed to read input file: {e}")
            self.master_app.hide_overlay()
            return

        if not search_terms_list:
            messagebox.showwarning("Input Warning", "Input file is empty or contains no valid search terms.")
            self.master_app.hide_overlay()
            return

        # Disable start button, enable stop button
        self.start_batch_button.config(state=tk.DISABLED)
        self.stop_batch_button.config(state=tk.NORMAL)

        print("INFO: Batch Process: Starting batch process...")
        # Pass the list of search terms directly, and remove output_folder from this call
        self.batch_processor.start_batch_processing(
            search_terms_list,  # Corrected: Pass the list of terms
            batch_location,
            selected_type,
            exact_match_mode,
            single_instance_mode,
            progress_callback=lambda msg: self.master_app.master.after(0, self.text_redirector.write, "INFO: " + msg),
            error_callback=lambda msg: self.master_app.master.after(0, messagebox.showerror, "Batch Error", msg),
            completion_callback=lambda all_results, was_stopped: self.master_app.master.after(0, self._on_batch_completion, all_results, was_stopped)
        )

    def stop_batch_process(self):
        """Signals the batch processing thread to stop."""
        self.batch_processor.stop_batch_processing()
        print("INFO: Batch Process: Stop requested.")

    def _on_batch_completion(self, all_batch_results, was_stopped):
        """Callback executed when the batch process completes."""
        self.master_app.hide_overlay() # Hide overlay from main app
        self.start_batch_button.config(state=tk.NORMAL)
        self.stop_batch_button.config(state=tk.DISABLED)
        
        # Display results and potentially export report
        self.display_batch_results(all_batch_results, was_stopped)

        # Export report only if output folder is specified and results exist
        output_folder = self.output_folder_entry.get().strip()
        if output_folder and all_batch_results:
            self.export_batch_report()

        self.text_redirector.flush() # Ensure all output is flushed
        print("INFO: Batch Process: Process completed (callback).")

    def display_batch_results(self, all_batch_results, was_stopped):
        """
        Displays the aggregated batch search results in the Text widget.
        Applies sorting based on current sort options.
        """
        self.last_batch_results = all_batch_results # Store for sorting/exporting
        self.path_tag_map = {} # Clear map for new display

        # Pass the tk.BooleanVar object directly, not its value
        formatted_segments = OutputFormatter.format_batch_search_results(
            all_batch_results, was_stopped, self.debug_info_var
        )

        self.output_text.config(state=tk.NORMAL) # Enable editing
        self.output_text.delete(1.0, tk.END) # Clear existing output
        
        for text, tag, raw_path in formatted_segments:
            if raw_path: # This segment is the first line of an item block and carries the raw_path
                unique_path_tag = f"path_{uuid.uuid4().hex}"
                self.path_tag_map[unique_path_tag] = raw_path # Store full path with unique tag
                self.output_text.insert(tk.END, text, (tag, unique_path_tag))
            else: # Regular text segment or segment not associated with a specific file path
                self.output_text.insert(tk.END, text, tag)
        
        self.output_text.config(state=tk.DISABLED) # Disable editing
        print("INFO: Batch Process: Results displayed.")


    def browse_input_file(self):
        """Opens a file dialog for selecting the batch input file."""
        filepath = filedialog.askopenfilename(
            parent=self.master_app.master,
            title="Select Batch Input File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            self.input_file_entry.delete(0, tk.END)
            self.input_file_entry.insert(0, filepath)
            print(f"INFO: Batch Process: Input file selected: {filepath}")
        else:
            print("INFO: Batch Process: Input file selection cancelled.")

    def browse_search_location(self):
        """Opens a directory dialog for selecting the folder to search."""
        folder_path = filedialog.askdirectory(
            parent=self.master_app.master,
            title="Select Folder to Search"
        )
        if folder_path:
            self.search_location_entry.delete(0, tk.END)
            self.search_location_entry.insert(0, folder_path)
            print(f"INFO: Batch Process: Search location selected: {folder_path}")
        else:
            print("INFO: Batch Process: Search location selection cancelled.")

    def browse_output_folder(self):
        """Opens a directory dialog for selecting the batch report output folder."""
        folderpath = filedialog.askdirectory(
            parent=self.master_app.master,
            title="Select Batch Report Output Folder"
        )
        if folderpath:
            self.output_folder_entry.delete(0, tk.END)
            self.output_folder_entry.insert(0, folderpath)
            print(f"INFO: Batch Process: Output folder selected: {folderpath}")
        else:
            print("INFO: Batch Process: Output folder selection cancelled.")

    def export_batch_report(self):
        """Exports the current batch search results to a text file."""
        if not self.last_batch_results:
            messagebox.showwarning("Export Warning", "No batch results to export.")
            return

        output_folder = self.output_folder_entry.get().strip()
        if not output_folder: # If optional output folder is left blank
            messagebox.showwarning("Export Warning", "No output folder specified. Skipping report export.")
            return

        if not os.path.isdir(output_folder):
            messagebox.showerror("Export Error", "Invalid output folder. Please select a valid folder or leave blank.")
            return

        # Generate a timestamped filename for the report
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"Batch_Search_Report_{timestamp}.txt"
        filepath = os.path.join(output_folder, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                # Iterate through the raw text content of the output_text widget
                # This ensures consistent formatting with what the user sees
                report_content = self.output_text.get(1.0, tk.END)
                f.write(report_content)
            messagebox.showinfo("Export Successful", f"Batch report exported to:\n{filepath}")
            print(f"INFO: Batch Process: Report exported to {filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report: {e}")
            print(f"ERROR: Batch Process: Failed to export report to {filepath}: {e}")

    def clear_batch_output(self):
        """Clears the batch output text area."""
        self.text_redirector.flush() # Ensure all pending messages are written before clearing
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.path_tag_map = {} # Clear the map
        print("INFO: Batch Process: Output area cleared.")


    def _get_filepath_at_cursor(self, event):
        """
        Attempts to extract a file path from the line under the mouse cursor in batch output.
        Retrieves the full path from the stored map using a unique tag.
        """
        try:
            index = self.output_text.index(f"@{event.x},{event.y}")
            # Get all tags at the clicked position
            tags_at_point = self.output_text.tag_names(index)
            
            for tag in tags_at_point:
                if tag.startswith("path_"): # Look for our special path tag
                    if tag in self.path_tag_map:
                        return self.path_tag_map[tag] # Return the full raw_path
            return None
        except tk.TclError:
            return None


    def _show_context_menu(self, event):
        """
        Displays a context menu when the output text area is right-clicked.
        The menu options are enabled/disabled based on whether a valid file path is found.
        """
        # Clear existing menu commands (important if menu is reused)
        self.context_menu = tk.Menu(self, tearoff=0) # Recreate menu to clear it
        
        # Always try to extract the filepath from the cursor's current position
        filepath = self._get_filepath_at_cursor(event)

        if filepath and os.path.exists(filepath):
            # If a valid file path is found, populate the menu with active commands
            self.context_menu.add_command(label="Open File Location", command=lambda: self._open_file_location(filepath))
            self.context_menu.add_command(label="Copy File Path", command=lambda: self._copy_filepath(filepath))
            self.context_menu.add_command(label="Open File", command=lambda: self._open_file(filepath))
        else:
            self.context_menu.add_command(label="No file path found", state=tk.DISABLED)
            
        try:
            # Display the menu at the mouse click position
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            # Make sure the menu is torn down properly
            self.context_menu.grab_release()

    def _open_file_location(self, filepath):
        """Opens the folder containing the given file in the OS file explorer."""
        folder_path = os.path.dirname(filepath)
        if not os.path.isdir(folder_path):
            messagebox.showerror("Error", f"Folder not found: {folder_path}")
            print(f"ERROR: Batch: Folder not found for opening: {folder_path}")
            return

        try:
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin": # macOS
                subprocess.run(["open", folder_path])
            else: # Linux and other POSIX-like systems
                subprocess.run(["xdg-open", folder_path])
            print(f"INFO: Batch: Opened folder: {folder_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")
            print(f"ERROR: Batch: Failed to open folder {folder_path}: {e}")

    def _copy_filepath(self, filepath):
        """Copies the given file path to the clipboard."""
        try:
            self.master_app.master.clipboard_clear() 
            self.master_app.master.clipboard_append(filepath)
            messagebox.showinfo("Copied", "File path copied to clipboard.")
            print(f"INFO: Batch: Copied to clipboard: {filepath}")
        except tk.TclError as e: # Catch Tkinter errors specific to clipboard
            messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
            print(f"ERROR: Batch: Failed to copy {filepath} to clipboard: {e}")

    def _open_file(self, filepath):
        """Opens the given file with its default application."""
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File not found: {filepath}")
            print(f"ERROR: Batch: File not found for opening: {filepath}")
            return
        
        try:
            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin": # macOS
                subprocess.run(["open", filepath])
            else: # Linux and other POSIX-like systems
                subprocess.run(["xdg-open", filepath])
            print(f"INFO: Batch: Opened file: {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")
            print(f"ERROR: Batch: Failed to open file {filepath}: {e}")
