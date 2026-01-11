# deck2trice

Multi-source MTG deck converter for Cockatrice. Import your Magic: The Gathering decks from Moxfield, Archidekt, and other online deck builders into Cockatrice format.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## Features

- Support for multiple deck sources (Moxfield, Archidekt)
- Batch import all decks or select specific ones
- Preserves deck metadata (commanders, formats, set codes, themes)
- Simple configuration file or CLI arguments
- Auto-sync workflow for keeping decks up-to-date

## Installation

```bash
pip install deck2trice
```

Or with uv:
```bash
uv pip install deck2trice
```

## Quick Start

Create `~/.deck2trice.yml`:

```yaml
username: your_username
source: archidekt  # or moxfield
fetch_all: true
deckpath: /path/to/cockatrice/decks
decks: []
```

Then run:

```bash
deck2trice
```

## Usage

### Basic Commands

```bash
# Use config file
deck2trice

# Override config settings
deck2trice --source moxfield --username yourname --all_decks

# Specify deck path
deck2trice --deckpath "/path/to/decks"

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
fetch_all: true                # true = all decks, false = specific decks only
deckpath: /path/to/decks       # Optional: Where to save .cod files
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

## Workflows

### Auto-Sync All Decks

```yaml
# ~/.deck2trice.yml
username: yourname
source: archidekt
fetch_all: true
deckpath: /path/to/cockatrice/decks
decks: []
```

Run `deck2trice` anytime to sync all decks.

### Specific Decks Only

```yaml
username: yourname
source: moxfield
fetch_all: false
deckpath: /path/to/decks
decks:
  - deck_id_1
  - deck_id_2
```

### One-Off Import

```bash
deck2trice --no_config --source archidekt --username user --all_decks --deckpath "./decks"
```

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

### Testing

```bash
uv run deck2trice
# or
uv run -m deck2trice.main --source archidekt --username yourname --all_decks
```

### Adding a New Source

1. Create a class inheriting from `DeckSource` in `deck2trice/core.py`
2. Implement `getUserDecks()`, `getDecklist()`, and `parse_deck()`
3. Add to `create_deck_source()` factory function
4. Submit a PR

## License

MIT License - see LICENSE file

## Credits

Inspired by [moxtrice](https://github.com/fecet/moxtrice) by Xie Zejian. This fork adds multi-source support and improved architecture.

## Support

- Issues: [GitHub Issues](https://github.com/liperium/deck2trice/issues)
- Discussions: [GitHub Discussions](https://github.com/liperium/deck2trice/discussions)
