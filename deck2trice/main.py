# %%
from pathlib import Path
import time
import platform
from typing import *

from absl import app, flags, logging
from ml_collections import config_flags
from tqdm import tqdm
from .core import create_deck_source
from ._version import __version__
from .utils import redirect_to_tqdm, relpath

FLAGS = flags.FLAGS

config_fp = (Path(__file__).parent / "config.py").resolve()
config_fp = relpath(config_fp, Path.cwd())

config_flags.DEFINE_config_file(
    "config",
    str(config_fp),
    "File path to the deck2trice configuration file.",
    lock_config=False,
)

def get_default_deckpath():
    """Get OS-specific default path for Cockatrice decks."""
    system = platform.system()
    if system == "Windows":
        # %LOCALAPPDATA%/Cockatrice/Cockatrice/decks
        localappdata = Path.home() / "AppData" / "Local"
        return str(localappdata / "Cockatrice" / "Cockatrice" / "decks")
    else:  # Linux, macOS, etc.
        # ~/.local/share/Cockatrice/Cockatrice/decks
        return str(Path.home() / ".local" / "share" / "Cockatrice" / "Cockatrice" / "decks")

flags.DEFINE_boolean("configure", False, "Configure the application for subsequent runs.")

flags.DEFINE_boolean("version", False, "Prints the version of the program and exits.")

flags.DEFINE_boolean("dryrun", False, "Test without writing to computer.")

flags.DEFINE_string("deckpath", get_default_deckpath(), "Where to save decklists")

flags.DEFINE_string("browser", "", "Which browser to impersonate for curl_cffi")

flags.DEFINE_string("source", "", "Deck source to use: 'moxfield' or 'archidekt'. Overrides config file.")

flags.DEFINE_string("username", "", "Username to fetch decks from. Overrides config file.")

flags.DEFINE_boolean("all_decks", False, "Fetch all decks from the user, ignoring the config file's deck list.")

flags.DEFINE_boolean("no_config", False, "Bypass config file reading and creation entirely. Requires --source and --username.")


def configure_interactive():
    """Interactive configuration setup."""
    print("deck2trice configuration wizard")

    # Ask for platform/source
    print("Which deck platform do you use?")
    print("1. Moxfield")
    print("2. Archidekt")
    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == "1":
            source = "moxfield"
            break
        elif choice == "2":
            source = "archidekt"
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")

    # Ask for username
    username = input(f"Enter your {source.capitalize()} username: ").strip()
    while not username:
        print("Username cannot be empty.")
        username = input(f"Enter your {source.capitalize()} username: ").strip()

    # Ask for deckpath
    default_deckpath = get_default_deckpath()
    print(f"Default deck save location: {default_deckpath}")
    custom_deckpath = input("Press Enter to use default, or enter a custom path: ").strip()
    deckpath = custom_deckpath if custom_deckpath else default_deckpath

    # Ask if they want to sync all decks
    while True:
        sync_all = input("\nDo you want to sync all your decks? (Y/n): ").strip().lower()
        if sync_all in ['n', 'no']:
            fetch_all = False
            print("Please configure the deck ids in the configuration file afterwards")
            break
        fetch_all = True
        break

    # Save configuration
    config_fp = Path.home() / ".deck2trice.yml"
    import yaml
    config_dict = {
        'source': source,
        'username': username,
        'deckpath': deckpath,
        'fetch_all': fetch_all,
        'decks': []
    }

    with open(config_fp, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False)

    print(f"\n✓ Configuration saved to {config_fp}")
    print("\nConfiguration complete! Run deck2trice again to sync your decks:")
    print("  deck2trice")
    print("\nUse --help to see available command-line options.")

def main(agrv):
    if FLAGS.version:
        return print(__version__)

    # Handle configure mode - exits after configuration
    if FLAGS.configure:
        configure_interactive()
        return

    # Handle no_config mode
    if FLAGS.no_config:
        if not FLAGS.source or not FLAGS.username:
            logging.error("--no_config requires both --source and --username to be specified")
            return
        source = FLAGS.source
        username = FLAGS.username
        config_decks = []
        config_fetch_all = False
        config_deckpath = ""
    else:
        config = FLAGS.config
        # Override config with CLI flags if provided
        source = FLAGS.source if FLAGS.source else config.source
        username = FLAGS.username if FLAGS.username else config.username
        config_decks = config.decks
        config_fetch_all = config.fetch_all
        config_deckpath = config.deckpath

    # Create the appropriate deck source client using factory
    client = create_deck_source(source, username)
    logging.info(f"Using deck source: {source}")

    # Determine if we should fetch all decks or use specific deck list
    fetch_all_mode = FLAGS.all_decks or config_fetch_all

    deck_ids = []

    # If we have specific decks in config and not in fetch_all mode, use only those
    if config_decks and not fetch_all_mode and not FLAGS.no_config:
        deck_ids = config_decks
        logging.info(f"Using {len(deck_ids)} deck(s) from config file")
    # Otherwise, fetch all decks from the user
    elif username:
        logging.info(f"Getting all decks for user {username}..")
        user_decks_response = client.getUserDecks()

        # Handle different response formats from different sources
        if source.lower() == "moxfield":
            deck_ids = [j["publicId"] for j in user_decks_response["data"]]
        elif source.lower() == "archidekt":
            # Archidekt returns deck objects directly in 'results'
            deck_ids = [str(j["id"]) for j in user_decks_response.get("results", [])]

        logging.info(f"Found {len(deck_ids)} deck(s) for user {username}")

    # Save/update config file if not in no_config mode
    if not FLAGS.no_config:
        config_fp = Path.home() / ".deck2trice.yml"

        # If config doesn't exist, or if user provided CLI flags, save/update it
        should_save = not config_fp.exists()
        if FLAGS.source or FLAGS.username or FLAGS.deckpath:
            should_save = True

        if should_save:
            # Update config with CLI flag values if provided
            if FLAGS.source:
                config.source = source
            if FLAGS.username:
                config.username = username
            if FLAGS.deckpath:
                config.deckpath = FLAGS.deckpath
            if FLAGS.all_decks or not config_decks:
                config.fetch_all = True
                config.decks = []

            # Save config
            import yaml
            config_dict = {
                'username': config.username,
                'source': config.source,
                'fetch_all': config.fetch_all,
                'deckpath': config.deckpath if config.deckpath else '',
                'decks': config.decks
            }
            with open(config_fp, "w") as f:
                yaml.dump(config_dict, f, default_flow_style=False)

            logging.info(f"Configuration saved to {config_fp}")

    # Determine deckpath: CLI flag takes priority, then config, then default
    deckpath = FLAGS.deckpath if FLAGS.deckpath else config_deckpath
    if deckpath:
        logging.info(f"Saving decks to: {deckpath}")

    jsonGets = []
    with redirect_to_tqdm(tqdm):
        for deck in tqdm(deck_ids, desc=f"Getting data from {source}"):
            logging.debug(f"Grabbing decklist <{deck}>")
            jsonGet = client.getDecklist(deck)
            jsonGets.append(jsonGet)
            # time.sleep(0.5)

        if not FLAGS.dryrun:
            for jsonGet in tqdm(jsonGets, desc="Converting deck to trice"):
                decklist = client.parse_deck(jsonGet)
                decklist.to_trice(Path(deckpath) if deckpath else Path(FLAGS.deckpath))


def absl_main():
    return app.run(main)


if __name__ == "__main__":
    absl_main()
