"""Text normalization utilities for consistent user input formatting.

Standardizes how user inputs are capitalized:
- Names (vendor, item, person): Title Case (each word capitalized)
- Addresses, descriptions: Sentence case (first letter capitalized only)
- Enum values, codes: UPPERCASE (preserved as-is)
"""


def title_case(text: str) -> str:
    """Convert text to title case (capitalize first letter of each word).
    
    Examples:
        "JOHN DOE" -> "John Doe"
        "apple juice" -> "Apple Juice"
        "coca cola inc" -> "Coca Cola Inc"
        "samsung 55\" tv" -> "Samsung 55\" Tv"
    """
    if not text or not isinstance(text, str):
        return text
    # Split by spaces and capitalize each word
    return " ".join(word.capitalize() for word in text.split())


def sentence_case(text: str) -> str:
    """Convert text to sentence case (capitalize first letter only).
    
    Examples:
        "john doe lives here" -> "John doe lives here"
        "APARTMENT 123" -> "Apartment 123"
        "enter your address" -> "Enter your address"
    """
    if not text or not isinstance(text, str):
        return text
    # Only capitalize the first character, lowercase the rest
    return text[0].upper() + text[1:].lower() if text else text


def normalize_vendor_name(name: str) -> str:
    """Normalize vendor name to title case."""
    return title_case(name) if name else name


def normalize_item_name(name: str) -> str:
    """Normalize item/product name to title case."""
    return title_case(name) if name else name


def normalize_person_name(name: str) -> str:
    """Normalize person name (contact person, user name) to title case."""
    return title_case(name) if name else name


def normalize_address(address: str) -> str:
    """Normalize address to sentence case."""
    return sentence_case(address) if address else address


def normalize_description(description: str) -> str:
    """Normalize description/notes to sentence case."""
    return sentence_case(description) if description else description


def normalize_city(city: str) -> str:
    """Normalize city name to title case."""
    return title_case(city) if city else city


def normalize_state(state: str) -> str:
    """Normalize state name to title case."""
    return title_case(state) if state else state
