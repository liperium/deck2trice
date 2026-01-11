from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import *
from abc import ABC, abstractmethod
import requests
import xml.etree.ElementTree as ET
import emoji
from pathvalidate import sanitize_filename
import re
import requests
from absl import logging
from .utils import _pretty_print
import random
import curl_cffi


@dataclass
class MTGCard:
    name: str
    quantity: int
    set_code: str = ""
    collector_number: str = ""
    uuid: str = ""

    @staticmethod
    def from_json(json: dict):
        pass
        # name.split(" // ")[0], attr["quantity"]
        # return MTGCard(json["name"], json["quantity"])


@dataclass
class DeckList:
    mainboard: List[MTGCard]
    name: str = ""
    description: str = ""
    format: str = ""
    companions: List[MTGCard] = field(default_factory=lambda: [])
    commanders: List[MTGCard] = field(default_factory=lambda: [])
    sideboard: List[MTGCard] = field(default_factory=lambda: [])
    maybeboard: List[MTGCard] = field(default_factory=lambda: [])
    tokens: List[MTGCard] = field(default_factory=lambda: [])
    themes: List[str] = field(default_factory=lambda: [])

    def to_trice(self, trice_path=Path("decks")):
        trice_path.mkdir(parents=True, exist_ok=True)
        # for card in self.companions + self.commanders:
        for card in self.commanders:
            self.sideboard.append(card)
        to_trice(
            self.mainboard,
            self.sideboard,
            self.name,
            self.description,
            commanders=self.commanders,
            deck_format=self.format,
            themes=self.themes,
            trice_path=trice_path,
        )

    @staticmethod
    def from_json(jsonGet, source="moxfield"):
        """Parse deck data from API response. Source can be 'moxfield' or 'archidekt'."""
        if source == "moxfield":
            return DeckList._parse_moxfield(jsonGet)
        elif source == "archidekt":
            return DeckList._parse_archidekt(jsonGet)
        else:
            raise ValueError(f"Unknown deck source: {source}")

    @staticmethod
    def _parse_moxfield(jsonGet):
        """Parse Moxfield API response"""
        name = jsonGet["name"]
        description = jsonGet["description"]
        mainboard_list = to_cards(jsonGet["mainboard"], source="moxfield")
        sideboard_list = to_cards(jsonGet["sideboard"], source="moxfield")
        # jsonGet['tokens']
        commanders = to_cards(jsonGet["commanders"], source="moxfield")
        companions = to_cards(jsonGet["companions"], source="moxfield")
        format = jsonGet["format"]
        themes = [theme["name"] for theme in jsonGet.get("hubs", [])]
        return DeckList(
            mainboard_list,
            name,
            description,
            format,
            sideboard=sideboard_list,
            commanders=commanders,
            companions=companions,
            themes=themes,
        )

    @staticmethod
    def _parse_archidekt(jsonGet):
        """Parse Archidekt API response"""
        name = jsonGet["name"]
        description = jsonGet.get("description", "")

        # Format mapping
        format_map = {
            3: "commander",
            1: "standard",
            2: "modern",
            # Add more as needed
        }
        deck_format = format_map.get(jsonGet.get("deckFormat"), "")

        # Group cards by category
        cards_by_category = {}
        for card_entry in jsonGet.get("cards", []):
            categories = card_entry.get("categories", [])
            for category in categories:
                if category not in cards_by_category:
                    cards_by_category[category] = []
                cards_by_category[category].append(card_entry)

        # Parse different card zones
        mainboard_list = []
        sideboard_list = []
        commanders = []
        companions = []
        maybeboard = []
        tokens = []

        # Get category metadata
        category_meta = {cat["name"]: cat for cat in jsonGet.get("categories", [])}

        for category_name, card_entries in cards_by_category.items():
            cat_info = category_meta.get(category_name, {})
            is_premier = cat_info.get("isPremier", False)
            included_in_deck = cat_info.get("includedInDeck", True)

            parsed_cards = to_cards_archidekt(card_entries)

            if category_name.lower() == "commander":
                commanders.extend(parsed_cards)
            elif category_name.lower() == "sideboard":
                sideboard_list.extend(parsed_cards)
            elif category_name.lower() == "maybeboard":
                maybeboard.extend(parsed_cards)
            elif "token" in category_name.lower() and not included_in_deck:
                tokens.extend(parsed_cards)
            elif included_in_deck and not is_premier:
                mainboard_list.extend(parsed_cards)

        # Extract themes from deck tags
        themes = [tag.get("name", "") for tag in jsonGet.get("deckTags", [])]

        return DeckList(
            mainboard_list,
            name,
            description,
            deck_format,
            sideboard=sideboard_list,
            commanders=commanders,
            companions=companions,
            maybeboard=maybeboard,
            tokens=tokens,
            themes=themes,
        )


user_agent_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; Trident/5.0)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0; MDDCJS)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)",
]


class DeckSource(ABC):
    """Abstract base class for deck source integrations (Moxfield, Archidekt, etc.)"""

    @abstractmethod
    def getUserDecks(self) -> dict:
        """Fetch all decks for the configured user. Returns JSON response."""
        pass

    @abstractmethod
    def getDecklist(self, deck_id: str) -> dict:
        """Fetch a specific deck by ID. Returns JSON response."""
        pass

    @abstractmethod
    def parse_deck(self, json_data: dict) -> "DeckList":
        """Parse API response into a DeckList object."""
        pass


@dataclass
class MoxField(DeckSource):
    username: str = ""

    # xmageFolderPath = ""
    def getUserDecks(self):
        url = (
            "https://api.moxfield.com/v2/users/"
            + self.username
            + "/decks?pageNumber=1&pageSize=99999"
        )
        # Logging
        # print(f"Grabbing <{self.username}>'s public decks from " + url)
        r = curl_cffi.get(url, impersonate="chrome", headers={'User-Agent': user_agent_list[random.randint(0, len(user_agent_list)-1)]})
        j = json.loads(r.text)
        # printJson(j)
        return j

    def getDecklist(self, deckId):
        # https://api.moxfield.com/v2/decks/all/g5uBDBFSe0OzEoC_jRInQw
        url = "https://api.moxfield.com/v2/decks/all/" + deckId
        # print(f"Grabbing decklist <{deckId}>")                        #Logging
        r = curl_cffi.get(url, impersonate="chrome", headers={'User-Agent': user_agent_list[random.randint(0, len(user_agent_list)-1)]})
        jsonGet = json.loads(r.text)
        return jsonGet

    def parse_deck(self, json_data: dict) -> "DeckList":
        """Parse Moxfield API response into DeckList"""
        return DeckList.from_json(json_data, source="moxfield")


@dataclass
class Archidekt(DeckSource):
    username: str = ""

    def getUserDecks(self):
        """Fetch all public decks for a user from Archidekt"""
        # Archidekt API v3 endpoint for user's decks
        url = f"https://archidekt.com/api/decks/v3/?ownerUsername={self.username}&pageSize=99999"
        r = curl_cffi.get(url, impersonate="chrome", headers={'User-Agent': user_agent_list[random.randint(0, len(user_agent_list)-1)]})
        j = json.loads(r.text)
        return j

    def getDecklist(self, deck_id: str):
        """Fetch a specific deck by ID from Archidekt"""
        url = f"https://archidekt.com/api/decks/{deck_id}/"
        r = curl_cffi.get(url, impersonate="chrome", headers={'User-Agent': user_agent_list[random.randint(0, len(user_agent_list)-1)]})
        jsonGet = json.loads(r.text)
        return jsonGet

    def parse_deck(self, json_data: dict) -> "DeckList":
        """Parse Archidekt API response into DeckList"""
        return DeckList.from_json(json_data, source="archidekt")


def create_deck_source(source: str, username: str = "") -> DeckSource:
    """Factory function to create a DeckSource instance based on the source type.

    Args:
        source: The deck source type ('moxfield' or 'archidekt')
        username: The username for the deck source

    Returns:
        A DeckSource instance (MoxField or Archidekt)

    Raises:
        ValueError: If the source type is unknown
    """
    source_lower = source.lower()
    if source_lower == "moxfield":
        return MoxField(username=username)
    elif source_lower == "archidekt":
        return Archidekt(username=username)
    else:
        raise ValueError(f"Unknown deck source: {source}. Supported sources: moxfield, archidekt")


def normlize_name(name):
    name = emoji.replace_emoji(name, "")
    name = re.sub(r"\\u[0-9a-fA-F]{4}", "", sanitize_filename(name))
    return name


def to_trice(
    mainboard_list: List[MTGCard],
    sideboard_list: List[MTGCard] = [],
    name="",
    description="",
    commanders: List[MTGCard] = [],
    deck_format=None,
    themes: List[str] = [],
    trice_path=Path("~/.local/share/Cockatrice/Cockatrice/decks"),
):
    root = ET.Element("cockatrice_deck")
    root.set("version", "1")

    deckname = ET.SubElement(root, "deckname")
    deckname.text = name

    # Add bannerCard element if there are commanders
    if commanders:
        bannercard = ET.SubElement(root, "bannerCard")
        bannercard.set("providerId", "")
        bannercard.text = commanders[0].name

    comments = ET.SubElement(root, "comments")
    comments.text = description

    # Add tags element for deck format and hubs
    tags = ET.SubElement(root, "tags")
    tag = ET.SubElement(tags, "tag")
    tag.text = "deck2trice"
    if deck_format != None:
        tag = ET.SubElement(tags, "tag")
        tag.text = deck_format.capitalize()
    # Add hub tags
    for theme in themes:
        tag = ET.SubElement(tags, "tag")
        tag.text = theme

    mainboard = ET.SubElement(root, "zone")
    mainboard.set("name", "main")

    for card in mainboard_list:
        card1 = ET.SubElement(mainboard, "card")
        card1.set("number", str(card.quantity))
        card1.set("name", card.name)
        if card.set_code:
            card1.set("setShortName", card.set_code)
        if card.collector_number:
            card1.set("collectorNumber", card.collector_number)
        if card.uuid:
            card1.set("uuid", card.uuid)

    sideboard = ET.SubElement(root, "zone")
    sideboard.set("name", "side")

    for card in sideboard_list:
        card1 = ET.SubElement(sideboard, "card")
        card1.set("number", str(card.quantity))
        card1.set("name", card.name)
        if card.set_code:
            card1.set("setShortName", card.set_code)
        if card.collector_number:
            card1.set("collectorNumber", card.collector_number)
        if card.uuid:
            card1.set("uuid", card.uuid)

    _pretty_print(root)
    tree = ET.ElementTree(root)
    # ET.indent(tree, space="\t", level=0)
    # trice_path=
    fp = trice_path / f"{normlize_name(name)}.cod"
    logging.debug(f"Writing to {fp}")
    tree.write(fp, encoding="UTF-8", xml_declaration=True)


def to_cards(raw_cards: dict, source="moxfield") -> List[MTGCard]:
    """Convert raw card data from Moxfield API to MTGCard objects"""
    cards = []
    for name, attr in raw_cards.items():
        # Determine the card name based on layout
        card_name = name
        if not (attr["card"]["layout"] == "split" or attr["card"]["layout"] == "adventure"):
            card_name = name.split(" // ")[0]

        # Extract set information
        quantity = attr["quantity"]
        set_code = attr["card"].get("set", "").upper()
        collector_number = attr["card"].get("cn", "")
        scryfall_id = attr["card"].get("scryfall_id", "")

        cards.append(MTGCard(
            name=card_name,
            quantity=quantity,
            set_code=set_code,
            collector_number=collector_number,
            uuid=scryfall_id
        ))

    return cards


def to_cards_archidekt(card_entries: List[dict]) -> List[MTGCard]:
    """Convert raw card data from Archidekt API to MTGCard objects"""
    cards = []
    for entry in card_entries:
        card_data = entry.get("card", {})
        quantity = entry.get("quantity", 1)

        # Get card name - use oracleCard.name if available, otherwise card.name
        oracle_card = card_data.get("oracleCard", {})
        card_name = oracle_card.get("name", card_data.get("name", "Unknown"))

        # Extract set information
        edition = card_data.get("edition", {})
        set_code = edition.get("editioncode", "").upper()
        collector_number = card_data.get("collectorNumber", "")

        # Get UUID from card data
        card_uuid = card_data.get("uid", "")

        cards.append(MTGCard(
            name=card_name,
            quantity=quantity,
            set_code=set_code,
            collector_number=collector_number,
            uuid=card_uuid
        ))

    return cards
