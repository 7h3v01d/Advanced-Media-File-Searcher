import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import subprocess
import threading
import time


# Assuming these are in the same directory or accessible via PYTHONPATH
# from base_parser import BaseParser # BaseParser is used by FileSearchService, not directly here
# from search_service import FileSearchService # This will be passed into the constructor
from gui_utilities import TextRedirector, format_bytes # Import from new utility file

class SearchTabFrame(tk.Frame):
    def __init__(self, parent_notebook, master_app_instance, search_service, text_redirector, debug_info_var, dark_mode_var):
        """
        Initializes the SearchTabFrame.

        Args:
            parent_notebook (ttk.Notebook): The notebook widget this tab will be added to.
            master_app_instance (FileSearchGUI): Reference to the main GUI application instance
                                                 for clipboard access, message boxes, and after calls.
            search_service (FileSearchService): The service responsible for performing file searches.
            text_redirector (TextRedirector): The custom stdout redirector for GUI logging.
            debug_info_var (tk.BooleanVar): A BooleanVar controlling debug output visibility.
            dark_mode_var (tk.BooleanVar): A BooleanVar controlling dark mode state.
        """
        super().__init__(parent_notebook)
        self.master_app = master_app_instance # Store reference to main app for shared functionalities
        self.search_service = search_service
        self.text_redirector = text_redirector
        self.debug_info_var = debug_info_var
        self.dark_mode_var = dark_mode_var # Store reference to the main app's dark_mode_var

        # Store the last search results for sorting and exporting
        self.last_search_results = []

        # Configure grid for this frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        for i in range(10): # 10 rows for widgets within the search tab
            self.grid_rowconfigure(i, weight=0)
        self.grid_rowconfigure(9, weight=1) # Output text area row gets weight


        # --- Widgets ---

        # 1. File Name Input
        self.file_name_label = tk.Label(self, text="Search Term (partial or full filename):")
        self.file_name_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        self.file_name_input_frame = tk.Frame(self)
        self.file_name_input_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 5))
        self.file_name_input_frame.grid_columnconfigure(0, weight=1) # Make entry expand
        self.file_name_input_frame.grid_columnconfigure(1, weight=0) # Paste button fixed width

        self.file_name_entry = tk.Entry(self.file_name_input_frame, width=60)
        self.file_name_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.file_name_entry.insert(0, "game of s04e04")

        self.paste_button = tk.Button(self.file_name_input_frame, text="Paste", command=self.paste_search_term,
                                      relief="raised", bd=2, padx=5, pady=2)
        self.paste_button.grid(row=0, column=1, sticky="e")


        # 2. Folder Location Input
        self.location_label = tk.Label(self, text="Folder to Search:")
        self.location_label.grid(row=2, column=0, sticky="w", padx=10, pady=(10, 0))

        self.location_entry = tk.Entry(self, width=60)
        self.location_entry.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))
        self.location_entry.insert(0, os.path.expanduser("~") if os.name == 'posix' else os.getcwd())

        self.browse_button = tk.Button(self, text="Browse Folder", command=self.browse_folder,
                                       relief="raised", bd=2, padx=10, pady=5)
        self.browse_button.grid(row=3, column=1, sticky="ew", padx=10, pady=(0, 5), columnspan=2)

        # 3. Search Type Selection (Radio Buttons)
        self.search_type_label = tk.Label(self, text="Filter by Content Type:")
        self.search_type_label.grid(row=4, column=0, sticky="w", padx=10, pady=(10, 0))

        self.radio_frame = tk.Frame(self)
        self.radio_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=(140, 10), pady=(10, 5))

        self.search_type_var = tk.StringVar(value="TV Show")
        self.radio_movie = tk.Radiobutton(self.radio_frame, text="Movie", variable=self.search_type_var, value="Movie")
        self.radio_movie.pack(side="left", padx=5)
        self.radio_tv_show = tk.Radiobutton(self.radio_frame, text="TV Show", variable=self.search_type_var, value="TV Show")
        self.radio_tv_show.pack(side="left", padx=5)
        self.radio_other = tk.Radiobutton(self.radio_frame, text="Other", variable=self.search_type_var, value="Other")
        self.radio_other.pack(side="left", padx=5)
        self.radio_all = tk.Radiobutton(self.radio_frame, text="All Categories", variable=self.search_type_var, value="All")
        self.radio_all.pack(side="left", padx=5)

        # 4. Checkbox Options
        self.checkbox_frame = tk.Frame(self)
        self.checkbox_frame.grid(row=5, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 5))

        # Dark Mode Checkbox (now back in search tab)
        self.dark_mode_checkbox = tk.Checkbutton(self.checkbox_frame, text="Dark Mode", variable=self.dark_mode_var,
                                  command=self.master_app.toggle_dark_mode) # Call main app's toggle method
        self.dark_mode_checkbox.pack(side="left", padx=5)

        # Debug Info Checkbox
        self.debug_info_checkbox = tk.Checkbutton(self.checkbox_frame, text="Show Debug Info", variable=self.debug_info_var)
        self.debug_info_checkbox.pack(side="left", padx=15)

        # Exact Match Checkbox
        self.exact_match_var = tk.BooleanVar(value=False) # Default to False (smart search)
        self.exact_match_checkbox = tk.Checkbutton(self.checkbox_frame, text="Exact Match", variable=self.exact_match_var)
        self.exact_match_checkbox.pack(side="left", padx=15)

        # 5. Result Sorting
        self.sort_frame = tk.Frame(self)
        self.sort_frame.grid(row=6, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 5))

        self.sort_label = tk.Label(self.sort_frame, text="Sort Results By:")
        self.sort_label.pack(side="left", padx=(0, 5))

        self.sort_option_var = tk.StringVar(value="Filename (Ascending)") # Default sort
        self.sort_options = [
            "Filename (Ascending)", "Filename (Descending)",
            "Size (Ascending)", "Size (Descending)",
            "Category (Ascending)", "Category (Descending)"
        ]
        self.sort_combobox = ttk.Combobox(self.sort_frame, textvariable=self.sort_option_var,
                                          values=self.sort_options, state="readonly", width=25)
        self.sort_combobox.pack(side="left", padx=5)
        self.sort_combobox.set(self.sort_options[0]) # Set default value


        # 6. Search and Stop Buttons
        self.button_row_frame = tk.Frame(self)
        self.button_row_frame.grid(row=7, column=0, columnspan=3, pady=15, padx=10, sticky="ew")
        self.button_row_frame.grid_columnconfigure(0, weight=1) # Search Button
        self.button_row_frame.grid_columnconfigure(1, weight=1) # Stop Button

        self.search_button = tk.Button(self.button_row_frame, text="Start Search", command=self.start_search_thread,
                                       relief="raised", bd=2, padx=20, pady=10, font=("TkDefaultFont", 10, "bold"))
        self.search_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.stop_button = tk.Button(self.button_row_frame, text="Stop Search", command=self.stop_search,
                                       relief="raised", bd=2, padx=20, pady=10, font=("TkDefaultFont", 10, "bold"),
                                      state=tk.DISABLED) # Initially disabled
        self.stop_button.grid(row=0, column=1, padx=5, sticky="ew")


        # 7. Output Area Header (Label + Clear Buttons)
        self.output_header_frame = tk.Frame(self)
        self.output_header_frame.grid(row=8, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 0))
        self.output_header_frame.grid_columnconfigure(0, weight=1) # For the label
        self.output_header_frame.grid_columnconfigure(1, weight=0) # For Clear Output button
        self.output_header_frame.grid_columnconfigure(2, weight=0) # For Clear All button

        self.output_label = tk.Label(self.output_header_frame, text="Search Output:")
        self.output_label.grid(row=0, column=0, sticky="w")

        self.clear_output_button = tk.Button(self.output_header_frame, text="Clear Output", command=self.clear_output_only,
                                            relief="raised", bd=2, padx=5, pady=2, font=("TkDefaultFont", 9))
        self.clear_output_button.grid(row=0, column=1, padx=(5, 5), sticky="e")

        self.clear_all_button = tk.Button(self.output_header_frame, text="Clear All", command=self.clear_all_fields_and_output,
                                       relief="raised", bd=2, padx=5, pady=2, font=("TkDefaultFont", 9)) # Adjust font/padding
        self.clear_all_button.grid(row=0, column=2, padx=(5, 0), sticky="e")


        # 8. Actual Output Text Area
        self.output_text = tk.Text(self, wrap="word", height=30, width=120, relief="sunken", bd=1)
        self.output_text.grid(row=9, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))

        self.output_scrollbar = tk.Scrollbar(self, command=self.output_text.yview)
        self.output_scrollbar.grid(row=9, column=2, sticky="ns", pady=(0, 10))
        self.output_text['yscrollcommand'] = self.output_scrollbar.set

        # Bind right-click event to the output text area (only one binding now)
        self.output_text.bind("<Button-3>", self._show_context_menu)

        # Context Menu for results
        self.context_menu = tk.Menu(self, tearoff=0)

        # Set the output text widget for the redirector
        self.text_redirector.set_output_text_widget(self.output_text)

    def apply_theme(self, theme, ttk_style):
        """Applies the current theme colors to all widgets within this tab."""
        # Apply theme to the main frame of the tab
        self.config(bg=theme["bg"])

        # Labels
        for label in [self.file_name_label, self.location_label, self.search_type_label, self.output_label, self.sort_label]:
            label.config(bg=theme["bg"], fg=theme["label_fg"])

        # Entries
        self.file_name_entry.config(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"])
        self.location_entry.config(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["entry_fg"])

        # Determine button foreground color based on theme
        button_fg_color = theme["button_fg"]

        # Buttons
        self.browse_button.config(bg=theme["button_bg"], fg=button_fg_color, activebackground=theme["button_bg"])
        self.paste_button.config(bg=theme["button_bg"], fg=button_fg_color, activebackground=theme["button_bg"])
        self.search_button.config(bg=theme["start_button_bg"], fg=button_fg_color, activebackground=theme["start_button_bg"])
        self.stop_button.config(bg=theme["stop_button_bg"], fg=button_fg_color, activebackground=theme["stop_button_bg"])
        self.clear_all_button.config(bg=theme["clear_button_bg"], fg=button_fg_color, activebackground=theme["clear_button_bg"])
        self.clear_output_button.config(bg=theme["clear_button_bg"], fg=button_fg_color, activebackground=theme["clear_button_bg"])

        # Radio Buttons (they are inside a frame)
        self.radio_frame.config(bg=theme["bg"])
        for radio in [self.radio_movie, self.radio_tv_show, self.radio_other, self.radio_all]:
            radio.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])

        # Checkboxes
        self.checkbox_frame.config(bg=theme["bg"])
        self.dark_mode_checkbox.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])
        self.debug_info_checkbox.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])
        self.exact_match_checkbox.config(bg=theme["bg"], fg=theme["radio_fg"], selectcolor=theme["entry_bg"])


        # Apply theme to other frames
        self.file_name_input_frame.config(bg=theme["bg"])
        self.button_row_frame.config(bg=theme["bg"])
        self.output_header_frame.config(bg=theme["bg"])
        self.sort_frame.config(bg=theme["bg"])

        # Output Text Area (general background/foreground)
        self.output_text.config(bg=theme["output_bg"], fg=theme["output_fg"])
        
        # Apply colors to specific output text tags
        self.output_text.tag_config("error", foreground=theme["error_fg"])
        self.output_text.tag_config("info", foreground=theme["info_fg"])
        self.output_text.tag_config("debug", foreground=theme["debug_fg"])
        self.output_text.tag_config("warning", foreground=theme["warning_fg"])
        self.output_text.tag_config("summary_not_found", foreground=theme["summary_not_found_fg"])
        self.output_text.tag_config("summary_found", foreground=theme["summary_found_fg"])
        self.output_text.tag_config("category_header", foreground=theme["category_header_fg"])
        self.output_text.tag_config("item_detail", foreground=theme["item_detail_fg"])
        self.output_text.tag_config("item_detail_parsed", foreground=theme["item_detail_parsed_fg"])
        
        # Style for the Combobox - Reverted to previous settings
        # Note: ttk_style is passed from the main app to ensure consistency for ttk widgets
        ttk_style.configure("TCombobox",
                             fieldbackground=theme["entry_bg"],
                             background=theme["button_bg"], # Dropdown button background
                             foreground=theme["entry_fg"],
                             selectbackground=theme["entry_bg"], # Background of selected item in dropdown list
                             selectforeground=theme["entry_fg"], # Foreground of selected item in dropdown list
                             bordercolor=theme["notebook_bg"],
                             arrowcolor=theme["entry_fg"]) # Arrow color
        ttk_style.map("TCombobox",
                       fieldbackground=[("readonly", theme["entry_bg"])],
                       background=[("readonly", theme["button_bg"])],
                       foreground=[("readonly", theme["entry_fg"])])


    def start_search_thread(self):
        """Starts the search in a separate thread by calling the search service."""
        # Use master_app for overlay and messageboxes
        self.master_app.show_overlay()
        
        # IMPORTANT: Flush any pending buffered messages BEFORE clearing the display
        self.text_redirector.flush()
        # Clear the output text area to remove all previous content, including old debug logs
        self.output_text.delete(1.0, tk.END) 
        
        print("INFO: GUI: Initiating search...")
        
        # Disable the search button and enable the stop button
        self.search_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        search_term = self.file_name_entry.get().strip()
        search_location = self.location_entry.get().strip()
        selected_type = self.search_type_var.get()
        # Retrieve the value for exact_match_mode from the checkbox
        exact_search_mode = self.exact_match_var.get() 

        if not search_term:
            messagebox.showerror("Input Error", "Please enter a search term.")
            print("ERROR: GUI: Search term not provided.")
            self.master_app.hide_overlay()
            self.search_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            return
        if not search_location:
            messagebox.showerror("Input Error", "Please select a folder to search.")
            print("ERROR: GUI: Search location not provided.")
            self.master_app.hide_overlay()
            self.search_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            return

        # Call the FileSearchService to start the search
        self.search_service.start_search(
            search_term=search_term,
            search_location=search_location,
            selected_type=selected_type,
            exact_match_mode=exact_search_mode,
            result_callback=lambda results, term, s_type: self.master_app.master.after(0, self.display_results, results, term, s_type),
            error_callback=lambda msg: self.master_app.master.after(0, messagebox.showerror, "Search Error", msg),
            completion_callback=lambda: self.master_app.master.after(0, self._on_search_completion)
        )

    def stop_search(self):
        """Signals the search service to stop."""
        self.search_service.stop_search()
        print("INFO: GUI: Stop search requested.")

    def _on_search_completion(self):
        """Callback executed when the search service indicates completion."""
        self.master_app.hide_overlay()
        self.search_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        # Ensure TextRedirector buffer is flushed on completion
        self.text_redirector.flush()
        print("INFO: GUI: Search process finished (callback).")

    def paste_search_term(self):
        """Pastes text from the clipboard into the search term entry."""
        try:
            clipboard_content = self.master_app.master.clipboard_get() # Use master_app.master for clipboard
            self.file_name_entry.delete(0, tk.END)
            self.file_name_entry.insert(0, clipboard_content)
            print(f"INFO: GUI: Pasted from clipboard: '{clipboard_content}'")
        except tk.TclError:
            messagebox.showwarning("Paste Error", "No content found in clipboard or clipboard is inaccessible.")
            print("WARNING: GUI: Failed to paste from clipboard.")

    def clear_output_only(self):
        """Clears only the output text area."""
        self.text_redirector.flush() # Ensure all pending messages are written before clearing
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        print("INFO: GUI: Output area cleared.")

    def clear_all_fields_and_output(self):
        """Clears all input fields and the output text area, resetting the UI."""
        self.file_name_entry.delete(0, tk.END)
        self.file_name_entry.insert(0, "") # Optionally insert default or leave blank

        # Reset location to default or clear it
        self.location_entry.delete(0, tk.END)
        self.location_entry.insert(0, os.path.expanduser("~") if os.name == 'posix' else os.getcwd())

        self.search_type_var.set("TV Show") # Reset radio button to default
        self.exact_match_var.set(False) # Uncheck exact match

        self.clear_output_only() # Call the new method to clear the output

        print("INFO: GUI: All search fields and output cleared.")
        # Ensure search button is enabled and stop button disabled
        self.search_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)


    def display_results(self, results_to_display, search_term, selected_type):
        """
        Displays the processed search results in the GUI's Text widget.
        Applies sorting based on current sort options.
        This method is called safely from the main thread via master.after.
        """
        self.last_search_results = results_to_display # Store results for potential sorting/exporting

        self.output_text.config(state=tk.NORMAL) # Enable editing
        self.output_text.delete(1.0, tk.END) # Clear existing output

        # --- Apply Sorting ---
        sorted_results = list(self.last_search_results) # Create a mutable copy
        sort_option = self.sort_option_var.get()

        if sorted_results:
            if "Filename" in sort_option:
                reverse_sort = "Descending" in sort_option
                sorted_results.sort(key=lambda x: os.path.basename(x['raw_path']).lower(), reverse=reverse_sort)
            elif "Size" in sort_option:
                reverse_sort = "Descending" in sort_option
                sorted_results.sort(key=lambda x: x['size_bytes'], reverse=reverse_sort)
            elif "Category" in sort_option:
                reverse_sort = "Descending" in sort_option
                sorted_results.sort(key=lambda x: x['category'].lower(), reverse=reverse_sort)


        if sorted_results:
            self.output_text.insert(tk.END, f"\nSearch Summary: Found {len(sorted_results)} '{selected_type}' files matching '{search_term}'.\n\n", "summary_found")
            for item in sorted_results:
                self.output_text.insert(tk.END, f"File: {os.path.basename(item['raw_path'])}\n", "category_header")
                self.output_text.insert(tk.END, f"  Path: {item['raw_path']}\n", "item_detail")
                self.output_text.insert(tk.END, f"  Size: {format_bytes(item['size_bytes'])}\n", "item_detail")
                self.output_text.insert(tk.END, f"  Category: {item['category']}\n", "item_detail")

                parsed_data = item.get("parsed_data", {})
                if item["category"] == "Movie":
                    title = parsed_data.get("title", "N/A")
                    year = parsed_data.get("year", "N/A")
                    resolution = parsed_data.get("resolution", "N/A")
                    self.output_text.insert(tk.END, f"  Parsed: Title='{title}', Year='{year}', Resolution='{resolution}'\n", "item_detail_parsed")
                elif item["category"] == "TV Show":
                    title = parsed_data.get("title", "N/A")
                    season = parsed_data.get("season", "N/A")
                    episode = parsed_data.get("episode", "N/A")
                    episode_title = parsed_data.get("episode_title", "N/A")
                    self.output_text.insert(tk.END, f"  Parsed: Title='{title}', Season={season}, Episode={episode}, Episode Title='{episode_title}'\n", "item_detail_parsed")
                else: # Other category
                    self.output_text.insert(tk.END, f"  (No specific media parsing data available)\n", "item_detail_parsed")
                self.output_text.insert(tk.END, "\n", "item_detail")

        else: # No files found
            self.output_text.insert(tk.END, f"\nSearch Summary: No '{selected_type}' files found matching '{search_term}'.\n", "summary_not_found")
        
        self.output_text.config(state=tk.DISABLED) # Disable editing
        print("INFO: GUI: Search results displayed.")


    def _get_filepath_at_cursor(self, event):
        """
        Attempts to extract a file path from the line under the mouse cursor.
        This function is now the primary way to get the path for the context menu.
        """
        try:
            # Get the index of the character at the event's coordinates
            index = self.output_text.index(f"@{event.x},{event.y}")
            # Get the start and end of the line
            line_start = self.output_text.index(index + " linestart")
            line_end = self.output_text.index(index + " lineend")
            # Get the full content of the line
            line_content = self.output_text.get(line_start, line_end)

            # Check if the line starts with "  Path: "
            if line_content.startswith("  Path: "):
                filepath = line_content[len("  Path: "):].strip()
                # Basic validation: check if it looks like a valid path
                if os.path.exists(filepath):
                    return filepath
            return None
        except tk.TclError:
            return None


    def _show_context_menu(self, event):
        """
        Displays a context menu when the output text area is right-clicked.
        The menu options are enabled/disabled based on whether a valid file path is found.
        """
        # Clear existing menu commands
        self.context_menu.delete(0, tk.END)
        
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
            print(f"ERROR: GUI: Folder not found for opening: {folder_path}")
            return

        try:
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin": # macOS
                subprocess.run(["open", folder_path])
            else: # Linux and other POSIX-like systems
                subprocess.run(["xdg-open", folder_path])
            print(f"INFO: GUI: Opened folder: {folder_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")
            print(f"ERROR: GUI: Failed to open folder {folder_path}: {e}")

    def _copy_filepath(self, filepath):
        """Copies the given file path to the clipboard."""
        try:
            self.master.clipboard_clear() 
            self.master.clipboard_append(filepath)
            messagebox.showinfo("Copied", "File path copied to clipboard.")
            print(f"INFO: GUI: Copied to clipboard: {filepath}")
        except tk.TclError as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
            print(f"ERROR: GUI: Failed to copy {filepath} to clipboard: {e}")

    def _open_file(self, filepath):
        """Opens the given file with its default application."""
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File not found: {filepath}")
            print(f"ERROR: GUI: File not found for opening: {filepath}")
            return
        
        try:
            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin": # macOS
                subprocess.run(["open", filepath])
            else: # Linux and other POSIX-like systems
                subprocess.run(["xdg-open", filepath])
            print(f"INFO: GUI: Opened file: {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")
            print(f"ERROR: GUI: Failed to open file {filepath}: {e}")


    def browse_folder(self):
        """Allows the user to select a directory."""
        selected_directory = filedialog.askdirectory(parent=self.master_app.master, # Changed from self.master
                                                     initialdir=self.location_entry.get() or os.getcwd(), # Corrected reference
                                                     title="Select Folder to Search")
        if selected_directory:
            self.location_entry.delete(0, tk.END) # Corrected reference
            self.location_entry.insert(0, selected_directory) # Corrected reference
            print(f"INFO: GUI: Folder selected: {selected_directory}")
        else:
            print("INFO: GUI: Folder selection cancelled.")


    def on_closing(self):
        """Called when the window is closed, restores original stdout."""
        # Attempt to stop any running search gracefully before closing
        self.search_service.stop_search()
        # Give a small moment for the thread to recognize the stop, if needed
        time.sleep(0.1) 
        sys.stdout = self.original_stdout
        self.master.destroy()

# --- Main execution block ---
if __name__ == "__main__":
    root = tk.Tk()
    # The following block was moved to gui_app.py
    # app = FileSearchGUI(root)
    # root.protocol("WM_DELETE_WINDOW", app.on_closing) # Handle window close event
    # root.mainloop()

