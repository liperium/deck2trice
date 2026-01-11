# %%
from pathlib import Path
import time
from typing import *

from absl import app, flags, logging
from ml_collections import config_flags
from tqdm import tqdm
from .core import create_deck_source
from ._version import __version__
from .utils import redirect_to_tqdm, relpath

FLAGS = flags.FLAGS
# card_name_exceptions = {"Brazen Borrower": "Brazen Borrower // Petty Theft"}
config_fp = (Path(__file__).parent / "config.py").resolve()
config_fp = relpath(config_fp, Path.cwd())
# print(config_fp)
config_flags.DEFINE_config_file(
    "config",
    str(config_fp),
    "File path to the training hyperparameter configuration.",
    lock_config=False,
)

flags.DEFINE_boolean("version", False, "Prints the version of the program and exits.")

flags.DEFINE_boolean("dryrun", False, "Test without writing to computer.")

flags.DEFINE_string("deckpath", "", "Where to save decklists")

flags.DEFINE_string("browser", "", "Which browser to impersonate for curl_cffi")

flags.DEFINE_string("source", "", "Deck source to use: 'moxfield' or 'archidekt'. Overrides config file.")

flags.DEFINE_string("username", "", "Username to fetch decks from. Overrides config file.")

flags.DEFINE_boolean("all_decks", False, "Fetch all decks from the user, ignoring the config file's deck list.")


def main(agrv):
    config = FLAGS.config

    if FLAGS.version:
        return print(__version__)

    # Override config with CLI flags if provided
    source = FLAGS.source if FLAGS.source else config.source
    username = FLAGS.username if FLAGS.username else config.username

    # Create the appropriate deck source client using factory
    client = create_deck_source(source, username)
    logging.info(f"Using deck source: {source}")

    deck_ids = []
    if username:
        logging.info(f"Getting lists of user {username}..")
        user_decks = client.getUserDecks()

        # Handle different response formats from different sources
        if source.lower() == "moxfield":
            deck_ids = [j["publicId"] for j in user_decks["data"]]
        elif source.lower() == "archidekt":
            # Archidekt returns deck objects directly in 'results'
            deck_ids = [str(j["id"]) for j in user_decks.get("results", [])]

    # Add specific decks from config unless --all_decks is specified
    if config.decks and not FLAGS.all_decks:
        deck_ids = list(set(config.decks + deck_ids))

    config_fp = Path.home() / ".moxtrice.yml"
    if not config_fp.exists():
        config.decks = deck_ids
        with open(config_fp, "w") as f:
            f.write(repr(config))

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
                decklist.to_trice(Path(FLAGS.deckpath))


def absl_main():
    return app.run(main)


if __name__ == "__main__":
    absl_main()
