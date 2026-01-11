# deck2trice

Multi-source MTG deck converter for Cockatrice. Import your Magic: The Gathering decks from **Moxfield**, **Archidekt**, and other online deck builders into Cockatrice format.* *Please note this has been mostly tested with the **Commander** format.*

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## Features

- Support for multiple deck sources (Moxfield, Archidekt)
- Batch import all decks or select specific ones
- Preserves deck metadata (commanders, formats, set codes, themes)
- Simple configuration file or CLI arguments
- Auto-sync workflow for keeping decks up-to-date

## Installation

### Pip (environment install)

```bash
pip install deck2trice
```

### UV (single run)

```bash
uv run deck2trice (command)
```

## Quick Start

### Easy Setup (Recommended)

Run once with your preferences - they'll be saved automatically:

```bash
deck2trice --source (moxfield|archidekt) --username yourname --deckpath /path/to/decks --all_decks
```

- The path to cockatrice decks is usually :

**Linux** : ~/.local/share/Cockatrice/Cockatrice/decks

**Windows** : "%LOCALAPPDATA%\Cockatrice\Cockatrice\decks

This will get all your public decks on run and parse them to cockatrice with ease!

From then on, just run:

```bash
deck2trice
```

### Manual Setup

Or create `~/.deck2trice.yml` manually:

```yaml
username: your_username
source: moxfield  # or 'archidekt'
fetch_all: true
deckpath: /path/to/cockatrice/decks
decks: []
```

## Usage

### Basic Commands

```bash
# Use config file
deck2trice

# One-off import without config file
deck2trice --no_config --source archidekt --username yourname --all_decks

# Test run without saving
deck2trice --dryrun
```

### Configuration File

Create `~/.deck2trice.yml` with these options:

```yaml
username: your_username        # Required: Your deck site username
source: archidekt              # Required: 'moxfield' or 'archidekt'
deckpath: /path/to/decks       # Optional: Where to save .cod files
fetch_all: true                # true = all decks, false = specific decks only
decks: []                      # Specific deck IDs (when fetch_all: false)
```

### CLI Flags

All flags override config file values:

- `--source <source>` - Deck source (moxfield or archidekt)
- `--username <name>` - Your username
- `--deckpath <path>` - Where to save decks
- `--all_decks` - Fetch all decks
- `--no_config` - Bypass config file
- `--dryrun` - Test without writing files
- `--version` - Show version

## Supported Sources

| Source | Status | Features |
|--------|--------|----------|
| Moxfield | Full Support | Decks, commanders, sideboards, themes |
| Archidekt | Full Support | Decks, commanders, categories, tags |

Want another source? Open an issue or submit a PR!

## Output Format

Generates `.cod` files for Cockatrice with:

- Deck name and description
- Commander(s) as banner cards
- Format tags
- Set codes and collector numbers
- Scryfall UUIDs
- Themes/tags
- Sideboard and maybeboard

## Development

### Setup

```bash
git clone https://github.com/liperium/deck2trice.git
cd deck2trice
uv sync
```

## License

Apache License 2.0 - see LICENSE file for details

## Credits

Inspired by [moxtrice](https://github.com/fecet/moxtrice) by Xie Zejian. This fork adds multi-source support and improved architecture.

## Support

- Issues: [GitHub Issues](https://github.com/liperium/deck2trice/issues)
- Discussions: [GitHub Discussions](https://github.com/liperium/deck2trice/discussions)
