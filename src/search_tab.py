import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import subprocess
import threading
import time # Import time module for sleep
import uuid # Import uuid for unique tags for context menu

# Import from new utility file
from gui_utilities import TextRedirector, format_bytes
from output_formatter import OutputFormatter # Import the new OutputFormatter

class SearchTabFrame(tk.Frame):
    def __init__(self, parent_notebook, master_app_instance, search_service, text_redirector, debug_info_var, dark_mode_var, default_search_location):
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
            default_search_location (str): The default folder path to use for searches.
        """
        super().__init__(parent_notebook)
        self.master_app = master_app_instance # Store reference to main app for shared functionalities
        self.search_service = search_service
        self.text_redirector = text_redirector
        self.debug_info_var = debug_info_var
        self.dark_mode_var = dark_mode_var # Store reference to the main app's dark_mode_var
        self.default_search_location = default_search_location # Store the passed default location

        # Store the last search results for sorting and exporting
        self.last_search_results = []
        # New: Dictionary to map unique tag names to full file paths for context menu
        self.path_tag_map = {} 


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
        self.file_name_entry.insert(0, "game of s04e04") # Keep initial example for user

        self.paste_button = tk.Button(self.file_name_input_frame, text="Paste", command=self.paste_search_term,
                                      relief="raised", bd=2, padx=5, pady=2)
        self.paste_button.grid(row=0, column=1, sticky="e")


        # 2. Folder Location Input
        self.location_label = tk.Label(self, text="Folder to Search:")
        self.location_label.grid(row=2, column=0, sticky="w", padx=10, pady=(10, 0))

        self.location_entry = tk.Entry(self, width=60)
        self.location_entry.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))
        # Set default value for search location from passed argument
        self.location_entry.insert(0, self.default_search_location)

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

        self.sort_combobox = ttk.Combobox(self.sort_frame, textvariable=tk.StringVar(value="Filename (Ascending)"),
                                          values=[
                                            "Filename (Ascending)", "Filename (Descending)",
                                            "Size (Ascending)", "Size (Descending)",
                                            "Category (Ascending)", "Category (Descending)"
                                          ],
                                          state="readonly", width=25)
        self.sort_combobox.pack(side="left", padx=5)
        self.sort_combobox.set("Filename (Ascending)") # Set default value


        # 6. Search and Stop Buttons
        self.button_row_frame = tk.Frame(self)
        self.button_row_frame.grid(row=7, column=0, columnspan=3, pady=15, padx=10, sticky="ew")
        self.button_row_frame.grid_columnconfigure(0, weight=1) # Search Button
        self.button_row_frame.grid_columnconfigure(1, weight=1) # Stop Button

        self.search_button = tk.Button(self.button_row_frame, text="Start Search", command=self.start_search_thread,
                                       relief="raised", bd=2, padx=20, pady=10, font=("TkDefaultFont", 12, "bold"))
        self.search_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.stop_button = tk.Button(self.button_row_frame, text="Stop Search", command=self.stop_search,
                                       relief="raised", bd=2, padx=20, pady=10, font=("TkDefaultFont", 12, "bold"),
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
        # Set a default monospace font here for better control over spacing and rendering
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


    def start_search_thread(self):
        """Starts the search in a separate thread by calling the search service."""
        # Use master_app for overlay and messageboxes
        self.master_app.show_overlay()
        
        # IMPORTANT: Flush any pending buffered messages BEFORE clearing the display
        self.text_redirector.flush()
        # Clear the output text area to remove all previous content, including old debug logs
        self.output_text.delete(1.0, tk.END) 
        # Clear the path map at the start of a new search
        self.path_tag_map = {} 
        
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
        if not os.path.isdir(search_location):
            messagebox.showerror("Input Error", f"Folder not found: {search_location}")
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
        self.path_tag_map = {} # Clear the map
        print("INFO: GUI: Output area cleared.")

    def clear_all_fields_and_output(self):
        """Clears all input fields and the search output area, resetting the UI."""
        self.file_name_entry.delete(0, tk.END)
        self.file_name_entry.insert(0, "") # Optionally insert default or leave blank

        # Reset location to default or clear it
        self.location_entry.delete(0, tk.END)
        self.location_entry.insert(0, self.default_search_location) # Use the passed default

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
        self.path_tag_map = {} # Reset map for new results

        # --- Apply Sorting ---
        sorted_results = list(self.last_search_results) # Create a mutable copy
        sort_option = self.sort_combobox.get() # Corrected: Get value from combobox directly

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

        # Use the new OutputFormatter to get the formatted list of (text, tag, raw_path_for_item) tuples
        formatted_segments = OutputFormatter.format_single_search_results(
            sorted_results, search_term, selected_type, self.debug_info_var
        )

        self.output_text.config(state=tk.NORMAL) # Enable editing
        self.output_text.delete(1.0, tk.END) # Clear existing output
        
        for text, tag, raw_path in formatted_segments:
            if raw_path: # This segment is the first line of an item block and carries the raw_path
                unique_path_tag = f"path_{uuid.uuid4().hex}"
                self.path_tag_map[unique_path_tag] = raw_path # Store full path with unique tag
                self.output_text.insert(tk.END, text, (tag, unique_path_tag))
            else: # Regular text segment
                self.output_text.insert(tk.END, text, tag)
        
        self.output_text.config(state=tk.DISABLED) # Disable editing
        print("INFO: GUI: Search results displayed.")


    def _get_filepath_at_cursor(self, event):
        """
        Attempts to extract a file path from the line under the mouse cursor.
        Now retrieves the full path from the stored map using a unique tag.
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
        except tk.TclError:
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
