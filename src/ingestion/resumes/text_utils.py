from __future__ import annotations

import re

from src.ingestion.resumes.models import ExperienceFacts, FactProvenance


class ParsedItem:
    def __init__(self, title: str | None, bullets: list[str]) -> None:
        self.title = title
        self.bullets = bullets


def extract_block_items(text: str, provenance: FactProvenance) -> list[ExperienceFacts]:
    items = extract_items(text)
    experiences: list[ExperienceFacts] = []
    for item in items:
        organization, title = split_title_line(item.title)
        experiences.append(
            ExperienceFacts(
                organization=organization,
                title=title,
                bullets=item.bullets,
                provenance=provenance,
            )
        )
    return experiences


def extract_items(text: str) -> list[ParsedItem]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    items: list[ParsedItem] = []
    current_title: str | None = None
    current_bullets: list[str] = []
    for line in lines:
        if is_bullet(line):
            current_bullets.append(strip_bullet(line))
            continue
        if current_title or current_bullets:
            items.append(ParsedItem(current_title, current_bullets))
        current_title = line
        current_bullets = []
    if current_title or current_bullets:
        items.append(ParsedItem(current_title, current_bullets))
    return items


def split_title_line(line: str | None) -> tuple[str | None, str | None]:
    if not line:
        return None, None
    for separator in (" | ", " - ", " — ", " at "):
        if separator in line:
            left, right = line.split(separator, 1)
            if separator == " at ":
                return right.strip(), left.strip()
            return left.strip(), right.strip()
    return line.strip(), None


def is_bullet(line: str) -> bool:
    return bool(re.match(r"^([-*•]|\d+[.)])\s+", line))


def strip_bullet(line: str) -> str:
    return re.sub(r"^([-*•]|\d+[.)])\s+", "", line).strip()


def split_skill_text(text: str) -> list[str]:
    chunks = re.split(r"[,;|•\n]", text)
    return sorted(
        {normalize_space(chunk) for chunk in chunks if normalize_space(chunk)}
    )


def extract_emails(text: str) -> list[str]:
    return sorted(set(re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)))


def extract_links(text: str) -> list[str]:
    return sorted(
        set(re.findall(r"https?://\S+|(?:github|linkedin)\.com/\S+", text, re.I))
    )


def extract_phone_numbers(text: str) -> list[str]:
    pattern = r"(?:\+?\d[\d\s().-]{7,}\d)"
    return sorted({normalize_space(match) for match in re.findall(pattern, text)})


def first_nonempty_line(text: str) -> str | None:
    for line in text.splitlines():
        normalized = normalize_space(line)
        if normalized:
            return normalized
    return None


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
