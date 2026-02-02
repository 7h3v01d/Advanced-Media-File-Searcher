import tkinter as tk
import os
import re # For log message parsing

# --- Custom Stream Redirection for GUI Output ---
class TextRedirector:
    """
    Redirects stdout to a tkinter.Text widget, allowing real-time logging
    and custom styling of messages (INFO, ERROR, DEBUG).
    Buffers messages and flushes in batches to improve performance.
    """
    def __init__(self, debug_var=None, buffer_limit=100): # Added buffer_limit
        self.widget = None  # Will be set later
        self.debug_var = debug_var # Link to the debug checkbox variable (tk.BooleanVar)
        self.buffer = [] # Initialize buffer to store (text, tag) tuples
        self.buffer_limit = buffer_limit # Number of lines to buffer before flushing
        self.after_id = None # To store ID of scheduled 'after' call for flushing

    def set_output_text_widget(self, widget):
        self.widget = widget
        # When the widget is set, apply initial default tag configs if needed,
        # but apply_theme will handle actual color mapping.
        # Add a check here to ensure self.widget is not None before calling tag_config
        if self.widget:
            self.widget.tag_config("stdout") # A default tag for general output

    def set_debug_mode(self, is_debug_enabled):
        """
        Sets the debug mode for the text redirector.
        Args:
            is_debug_enabled (bool): True to enable debug messages, False to disable.
        """
        # Ensure debug_var is a BooleanVar before setting its value
        if self.debug_var and isinstance(self.debug_var, tk.BooleanVar):
            self.debug_var.set(is_debug_enabled)
        elif self.debug_var is None:
            # If debug_var wasn't provided, we can still internally manage a debug state
            # This handles cases where debug_var is not directly linked to a Tkinter var
            self._internal_debug_state = is_debug_enabled
        # If debug_var is a bool directly, it implies it's not a Tkinter variable,
        # so we can't call .set() on it. This is why we introduced the check for isinstance(tk.BooleanVar)

    def write(self, text):
        """
        Writes text to the widget, applying specific tags based on prefixes.
        Buffers output and flushes periodically to optimize GUI updates.
        """
        if not self.widget: # Ensure widget is set before attempting to write
            return

        # Suppress "Found:" messages from filetracker as GUI will format its own detailed output
        if text.strip().startswith("Found:"):
            return

        tag = "stdout" # Default tag

        # Determine tag based on message content
        if text.startswith("ERROR:"):
            tag = "error"
        elif text.startswith("INFO:"):
            tag = "info"
        elif text.startswith("DEBUG:"):
            # Only append debug messages if debug_var is True
            # Check if debug_var is a BooleanVar first, then get its value
            if self.debug_var and isinstance(self.debug_var, tk.BooleanVar):
                if not self.debug_var.get():
                    return # Suppress debug message if debug mode is off
            # Fallback for older configurations or non-tk.BooleanVar debug_var
            elif self.debug_var is False or (hasattr(self, '_internal_debug_state') and not self._internal_debug_state):
                 return # Suppress if debug is explicitly False or internal state is False
            tag = "debug"
        elif text.startswith("WARNING:"):
            tag = "warning"
        
        self.buffer.append((text, tag))

        # Schedule a flush if the buffer limit is reached or if no flush is already scheduled
        if len(self.buffer) >= self.buffer_limit and not self.after_id:
            # Use self.widget.after to schedule flush on the main Tkinter thread
            self.after_id = self.widget.after(10, self.flush_buffer)
        elif not self.after_id:
            # If buffer not full, but no flush scheduled, schedule a small delay flush
            self.after_id = self.widget.after(10, self.flush_buffer)


    def flush_buffer(self):
        """
        Inserts all buffered text into the widget and clears the buffer.
        Configures widget state only once per batch.
        """
        # Clear any pending scheduled flush to prevent it from firing after manual flush
        # Add a check for self.widget before calling after_cancel
        if self.after_id and self.widget:
            self.widget.after_cancel(self.after_id)
            self.after_id = None

        if not self.buffer: # Nothing to flush
            return

        # Add a check here to ensure self.widget is not None before configuring
        if self.widget:
            self.widget.config(state=tk.NORMAL) # Enable editing once for the entire batch
            for text, tag in self.buffer:
                self.widget.insert(tk.END, text, tag)
            self.buffer = [] # Clear the buffer after inserting

            self.widget.config(state=tk.DISABLED) # Disable editing once after the entire batch
            self.widget.see(tk.END) # Auto-scroll once after all inserts

    def flush(self):
        """
        Required for stdout redirection. Ensures all remaining buffered messages are written.
        This will be called when sys.stdout is about to be read, or when a program exits.
        """
        self.flush_buffer()

# --- Helper function for human-readable file sizes ---
def format_bytes(size_bytes):
    """Converts a size in bytes to a human-readable format (KB, MB, GB, TB)."""
    if size_bytes < 0:
        return "N/A" # For cases where size retrieval failed
    if size_bytes == 0:
        return "0 Bytes"
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {units[i]}"
