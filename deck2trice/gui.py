"""Modern GUI for deck2trice using tkinter."""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from pathlib import Path
import threading
import yaml

from .core import create_deck_source
from .main import get_default_deckpath
from ._version import __version__


class Deck2TriceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"deck2trice v{__version__}")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)

        # Set theme
        self.style = ttk.Style()
        # Try to use a modern theme if available
        available_themes = self.style.theme_names()
        if 'vista' in available_themes:
            self.style.theme_use('vista')
        elif 'clam' in available_themes:
            self.style.theme_use('clam')

        # Configure custom styles
        self.style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'))
        self.style.configure('Subtitle.TLabel', font=('Segoe UI', 10))
        self.style.configure('Action.TButton', font=('Segoe UI', 11, 'bold'), padding=10)
        self.style.configure('Card.TFrame', relief='solid', borderwidth=1)

        # Load existing config
        self.config_fp = Path.home() / ".deck2trice.yml"
        self.config = self.load_config()

        # Create header
        self.create_header()

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        # Create tabs
        self.config_frame = ttk.Frame(self.notebook, padding=20)
        self.sync_frame = ttk.Frame(self.notebook, padding=20)

        self.notebook.add(self.config_frame, text="  Configuration  ")
        self.notebook.add(self.sync_frame, text="  Sync Decks  ")

        self.setup_config_tab()
        self.setup_sync_tab()

        # Center window on screen
        self.center_window()

    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_header(self):
        """Create app header."""
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=20, pady=(20, 10))

        title_label = ttk.Label(header_frame, text="deck2trice", style='Title.TLabel')
        title_label.pack(side='left')

        version_label = ttk.Label(header_frame, text=f"v{__version__}", style='Subtitle.TLabel',
                                 foreground='gray')
        version_label.pack(side='left', padx=(10, 0))

        subtitle = ttk.Label(header_frame, text="MTG Deck Sync for Cockatrice",
                            style='Subtitle.TLabel', foreground='gray')
        subtitle.pack(side='right')

    def load_config(self):
        """Load existing configuration from file."""
        default_config = {
            'source': 'moxfield',
            'username': '',
            'deckpath': get_default_deckpath(),
            'fetch_all': True,
            'decks': []
        }

        if self.config_fp.exists():
            try:
                with open(self.config_fp, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        default_config.update(loaded_config)
            except Exception as e:
                print(f"Error loading config: {e}")

        return default_config

    def setup_config_tab(self):
        """Setup the configuration tab with modern styling."""
        frame = self.config_frame

        # Instructions
        instructions = ttk.Label(frame,
                                text="Configure your deck source and preferences",
                                font=('Segoe UI', 10),
                                foreground='gray')
        instructions.pack(pady=(0, 20))

        # Form container
        form_frame = ttk.Frame(frame)
        form_frame.pack(fill='both', expand=True)

        # Platform/Source
        platform_label = ttk.Label(form_frame, text="Deck Platform", font=('Segoe UI', 10, 'bold'))
        platform_label.grid(row=0, column=0, sticky='w', pady=(0, 5))

        self.source_var = tk.StringVar(value=self.config['source'])
        source_combo = ttk.Combobox(form_frame, textvariable=self.source_var,
                                    values=['moxfield', 'archidekt'],
                                    state='readonly', width=40, font=('Segoe UI', 10))
        source_combo.grid(row=1, column=0, sticky='ew', pady=(0, 20))

        # Username
        username_label = ttk.Label(form_frame, text="Username", font=('Segoe UI', 10, 'bold'))
        username_label.grid(row=2, column=0, sticky='w', pady=(0, 5))

        self.username_var = tk.StringVar(value=self.config['username'])
        username_entry = ttk.Entry(form_frame, textvariable=self.username_var,
                                   width=42, font=('Segoe UI', 10))
        username_entry.grid(row=3, column=0, sticky='ew', pady=(0, 20))

        # Deck path
        path_label = ttk.Label(form_frame, text="Deck Save Location", font=('Segoe UI', 10, 'bold'))
        path_label.grid(row=4, column=0, sticky='w', pady=(0, 5))

        path_container = ttk.Frame(form_frame)
        path_container.grid(row=5, column=0, sticky='ew', pady=(0, 20))

        self.deckpath_var = tk.StringVar(value=self.config['deckpath'])
        deckpath_entry = ttk.Entry(path_container, textvariable=self.deckpath_var,
                                   font=('Segoe UI', 9))
        deckpath_entry.pack(side='left', fill='x', expand=True)

        browse_btn = ttk.Button(path_container, text="Browse...", command=self.browse_path)
        browse_btn.pack(side='left', padx=(10, 0))

        # Fetch all decks checkbox
        fetch_frame = ttk.Frame(form_frame)
        fetch_frame.grid(row=6, column=0, sticky='w', pady=(0, 30))

        self.fetch_all_var = tk.BooleanVar(value=self.config['fetch_all'])
        fetch_all_check = ttk.Checkbutton(fetch_frame, text="Sync all decks from user",
                                         variable=self.fetch_all_var)
        fetch_all_check.pack(side='left')

        help_label = ttk.Label(fetch_frame, text="(Recommended)",
                              foreground='gray', font=('Segoe UI', 9))
        help_label.pack(side='left', padx=(5, 0))

        # Configure grid weights
        form_frame.columnconfigure(0, weight=1)

        # Save button
        button_frame = ttk.Frame(frame)
        button_frame.pack(side='bottom', fill='x', pady=(20, 0))

        save_btn = ttk.Button(button_frame, text="Save Configuration",
                             command=self.save_config, style='Action.TButton')
        save_btn.pack()

        # Status label
        self.config_status = ttk.Label(button_frame, text="", font=('Segoe UI', 9))
        self.config_status.pack(pady=(10, 0))

    def setup_sync_tab(self):
        """Setup the sync tab with modern styling."""
        frame = self.sync_frame

        # Info card
        info_card = ttk.Frame(frame, style='Card.TFrame', padding=15)
        info_card.pack(fill='x', pady=(0, 20))

        info_title = ttk.Label(info_card, text="Current Configuration",
                              font=('Segoe UI', 10, 'bold'))
        info_title.pack(anchor='w')

        separator = ttk.Separator(info_card, orient='horizontal')
        separator.pack(fill='x', pady=10)

        self.info_label = ttk.Label(info_card,
                                    text=self.get_config_info(),
                                    justify='left',
                                    font=('Segoe UI', 9))
        self.info_label.pack(anchor='w')

        # Sync button
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)

        self.sync_btn = ttk.Button(button_frame, text="⬇ Sync Decks Now",
                                   command=self.sync_decks, style='Action.TButton')
        self.sync_btn.pack()

        # Progress bar
        self.progress = ttk.Progressbar(frame, mode='indeterminate', length=400)
        self.progress.pack(pady=(0, 20))

        # Output section
        output_label = ttk.Label(frame, text="Sync Log", font=('Segoe UI', 10, 'bold'))
        output_label.pack(anchor='w', pady=(0, 5))

        # Output text area with better styling
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill='both', expand=True)

        self.output_text = scrolledtext.ScrolledText(text_frame,
                                                     height=12,
                                                     font=('Consolas', 9),
                                                     wrap=tk.WORD,
                                                     bg='#f5f5f5',
                                                     relief='solid',
                                                     borderwidth=1)
        self.output_text.pack(fill='both', expand=True)

    def get_config_info(self):
        """Get formatted config info text."""
        username = self.config.get('username', 'Not configured')
        source = self.config.get('source', 'Not configured')
        deckpath = self.config.get('deckpath', 'Not configured')
        fetch_all = "Yes" if self.config.get('fetch_all', False) else "No"

        return f"Platform: {source.capitalize()}\nUsername: {username}\nSync all decks: {fetch_all}\nSave location: {deckpath}"

    def browse_path(self):
        """Open directory browser."""
        directory = filedialog.askdirectory(
            initialdir=self.deckpath_var.get(),
            title="Select Deck Save Location"
        )
        if directory:
            self.deckpath_var.set(directory)

    def save_config(self):
        """Save configuration to file."""
        try:
            # Validate username
            if not self.username_var.get().strip():
                messagebox.showwarning("Validation Error", "Username cannot be empty!")
                return

            config_dict = {
                'source': self.source_var.get(),
                'username': self.username_var.get().strip(),
                'deckpath': self.deckpath_var.get(),
                'fetch_all': self.fetch_all_var.get(),
                'decks': []
            }

            with open(self.config_fp, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)

            self.config = config_dict
            self.config_status.config(text="✓ Configuration saved successfully!",
                                     foreground="green")

            # Update sync tab info
            self.info_label.config(text=self.get_config_info())

            # Show success message
            messagebox.showinfo("Success", "Configuration saved successfully!")

        except Exception as e:
            self.config_status.config(text=f"✗ Error: {str(e)}", foreground="red")
            messagebox.showerror("Error", f"Failed to save configuration:\n{str(e)}")

    def log_output(self, message, tag=None):
        """Write message to output text area."""
        self.output_text.insert(tk.END, message + "\n", tag)
        self.output_text.see(tk.END)
        self.root.update_idletasks()

    def sync_decks(self):
        """Run deck sync in a background thread."""
        if not self.config.get('username'):
            messagebox.showwarning("Configuration Required",
                                 "Please configure your username in the Configuration tab first!")
            self.notebook.select(0)  # Switch to config tab
            return

        # Disable sync button
        self.sync_btn.config(state='disabled', text="Syncing...")
        self.progress.start(10)
        self.output_text.delete(1.0, tk.END)

        # Run sync in thread
        thread = threading.Thread(target=self.run_sync, daemon=True)
        thread.start()

    def run_sync(self):
        """Actual sync logic running in background thread."""
        try:
            source = self.config['source']
            username = self.config['username']
            deckpath = Path(self.config['deckpath'])
            fetch_all = self.config['fetch_all']

            self.log_output(f"🔗 Connecting to {source.capitalize()}...")
            client = create_deck_source(source, username)

            self.log_output(f"📥 Fetching decks for user '{username}'...")
            user_decks_response = client.getUserDecks()

            # Get deck IDs based on source
            if source.lower() == "moxfield":
                deck_ids = [j["publicId"] for j in user_decks_response["data"]]
            elif source.lower() == "archidekt":
                deck_ids = [str(j["id"]) for j in user_decks_response.get("results", [])]
            else:
                deck_ids = []

            self.log_output(f"✓ Found {len(deck_ids)} deck(s)\n")

            if not deck_ids:
                self.log_output("⚠ No decks found to sync.")
                return

            # Fetch and convert each deck
            for i, deck_id in enumerate(deck_ids, 1):
                self.log_output(f"[{i}/{len(deck_ids)}] Processing deck {deck_id}...")

                jsonGet = client.getDecklist(deck_id)
                decklist = client.parse_deck(jsonGet)
                decklist.to_trice(deckpath)

            self.log_output(f"\n✓ Success! {len(deck_ids)} deck(s) synced to:")
            self.log_output(f"  {deckpath}")

            # Show success dialog
            self.root.after(0, lambda: messagebox.showinfo(
                "Sync Complete",
                f"Successfully synced {len(deck_ids)} deck(s)!\n\nSaved to:\n{deckpath}"
            ))

        except Exception as e:
            self.log_output(f"\n✗ Error: {str(e)}")
            import traceback
            self.log_output("\nStack trace:")
            self.log_output(traceback.format_exc())

            # Show error dialog
            self.root.after(0, lambda: messagebox.showerror(
                "Sync Failed",
                f"An error occurred during sync:\n\n{str(e)}"
            ))

        finally:
            # Re-enable sync button
            self.progress.stop()
            self.sync_btn.config(state='normal', text="⬇ Sync Decks Now")


def main():
    """Entry point for the GUI application."""
    root = tk.Tk()
    app = Deck2TriceGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
