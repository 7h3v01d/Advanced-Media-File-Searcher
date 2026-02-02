import tkinter as tk
import os

# --- Custom Stream Redirection for GUI Output ---
class TextRedirector:
    """
    Redirects stdout to a tkinter.Text widget, allowing real-time logging
    and custom styling of messages (INFO, ERROR, DEBUG).
    Buffers messages and flushes in batches to improve performance.
    """
    def __init__(self, debug_var=None, buffer_limit=100): # Added buffer_limit
        self.widget = None  # Will be set later
        self.debug_var = debug_var # Link to the debug checkbox variable
        self.buffer = [] # Initialize buffer to store (text, tag) tuples
        self.buffer_limit = buffer_limit # Number of lines to buffer before flushing
        self.after_id = None # To store ID of scheduled 'after' call for flushing

    def set_output_text_widget(self, widget):
        self.widget = widget
        # When the widget is set, apply initial default tag configs if needed,
        # but apply_theme will handle actual color mapping.
        self.widget.tag_config("stdout") # A default tag for general output

    def write(self, text):
        """
        Writes text to the widget, applying specific tags based on prefixes.
        Buffers output and flushes periodically to optimize GUI updates.
        """
        if not self.widget: # Ensure widget is set before attempting to write
            return

        # Suppress "Found:" messages from filetracker as GUI will format its own detailed output
        if text.startswith("Found:"):
            return

        # Determine if this is a debug message and if it should be suppressed
        is_debug_message = text.startswith("DEBUG:")
        # Only suppress debug messages if the debug_var exists and is explicitly set to False
        should_suppress_debug = is_debug_message and (self.debug_var and not self.debug_var.get())

        if should_suppress_debug:
            return # Skip insertion entirely for suppressed debug messages

        # Ensure that even empty lines or just newlines don't create unwanted blank spaces
        # if they are not explicitly intended to be part of the output flow.
        # This prevents excessive blank lines from prints that are just newlines.
        if text.strip() == "" and text == "\n":
             return

        # Determine the tag based on the message prefix
        applied_tag = "stdout" # Default general tag
        if is_debug_message:
            applied_tag = "debug"
        elif text.startswith("ERROR:"):
            applied_tag = "error"
        elif text.startswith("INFO:"):
            applied_tag = "info"
        elif text.startswith("WARNING:"):
            applied_tag = "warning"
        
        # Ensure a newline for each distinct write call if it doesn't already have one
        if not text.endswith('\n'):
            text += '\n'

        # Append to buffer instead of immediate insert
        self.buffer.append((text, applied_tag))

        # If buffer limit is reached or if it's an error/warning (urgent message), flush immediately
        # Error/warning messages are flushed immediately for immediate user feedback.
        if len(self.buffer) >= self.buffer_limit or applied_tag in ["error", "warning"]:
            self.flush_buffer()
        else:
            # Schedule a small delay to flush the buffer if no more writes come in quickly.
            # We cancel any previously scheduled flush to avoid redundant calls if writes are rapid.
            if self.after_id:
                self.widget.after_cancel(self.after_id)
            # Schedule flush after a short delay (e.g., 50ms)
            self.after_id = self.widget.after(50, self.flush_buffer)

    def flush_buffer(self):
        """
        Processes and inserts buffered messages into the Text widget.
        Optimizes by enabling/disabling widget state only once per batch.
        """
        # Clear any pending scheduled flush to prevent it from firing after manual flush
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None

        if not self.buffer: # Nothing to flush
            return

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

