import re


def parse_item_and_amount(text: str) -> tuple[str, str | None]:
    """
    Ищет в конце строки количество (например: "Молоко 2 шт", "Хлеб 1б")
    """
    match = re.search(
        r"(\d+(?:[\.,]\d+)?)\s*(шт|кг|гр|г|л|мл|б|уп|пак)\.?\s*$", text, re.IGNORECASE
    )
    if match:
        amount_val = match.group(1)
        amount_unit = match.group(2)
        amount_str = f"{amount_val} {amount_unit.lower()}"
        clean_text = text[: match.start()].strip()
        return clean_text, amount_str
    return text, None
