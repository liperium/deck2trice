from ml_collections import ConfigDict
from pathlib import Path
import yaml


def get_config():
    config = ConfigDict()
    config.username = "facet"
    config.decks = []
    config.source = "moxfield"  # Default deck source: 'moxfield' or 'archidekt'
    config.fetch_all = (
        True  # If True, always fetch all decks from user (ignores decks list)
    )
    config.deckpath = ""  # Default path to save decks (empty uses default)

    config_fp = Path.home() / ".deck2trice.yml"
    if config_fp.exists():
        with open(config_fp, "r") as f:
            conf = yaml.load(f.read(), yaml.UnsafeLoader)
        config.update(conf)

    return config
