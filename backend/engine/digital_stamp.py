from __future__ import annotations

import hashlib


class DigitalStampGenerator:
    PATTERNS = [" /\\ ", " || ", " <> ", " ~~ ", " [] "]

    def generate(self, content: str, persona_name: str) -> str:
        digest = hashlib.sha256(f"{persona_name}:{content}".encode()).hexdigest()
        rows = []
        for index in range(0, 12, 3):
            part = digest[index : index + 3]
            row = "".join(self.PATTERNS[int(char, 16) % len(self.PATTERNS)] for char in part)
            rows.append(row)
        return "\n".join(rows)
