import re

class PIIScrubber:
    def __init__(self, mask="***"):
        self.mask = mask
        self.patterns = {
            "email": re.compile(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
            ),
            "phone": re.compile(
                r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"
            ),
            "ssn": re.compile(
                r"\b\d{3}-\d{2}-\d{4}\b"
            ),
            "credit_card": re.compile(
                r"\b(?:\d[ -]*?){13,16}\b"
            ),
            "ip_address": re.compile(
                r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
            ),
        }
        # PII labels to erase
        self.label_pattern = re.compile(
            r"\b(email|e-mail|ssn|social\s+security|ip\s*address|credit\s*card)\b",
            re.IGNORECASE
        )

    def scrub(self, text: str) -> str:
        """
        Replace detected PII in text with a mask.
        """
        if not isinstance(text, str):
            raise TypeError("Input must be a string")

        scrubbed = text
        for pattern in self.patterns.values():
            scrubbed = pattern.sub(self.mask, scrubbed)

        # Remove PII labels
        scrubbed = self.label_pattern.sub(self.mask, scrubbed)

        # Normalize spacing around masks
        scrubbed = re.sub(rf"\s*{re.escape(self.mask)}\s*", f" {self.mask} ", scrubbed)
        scrubbed = re.sub(r"\s+([.,])", r"\1", scrubbed)
        scrubbed = re.sub(r"\s{2,}", " ", scrubbed)

        return scrubbed.strip()

    def scrub_data(self, data):
        """
        Recursively scrub all strings in a nested dict/list structure using your existing scrub(text) function.
        Non-strings are converted to strings before scrubbing.
        """
        if isinstance(data, str):
            return self.scrub(data)  # your original scrub function
        elif isinstance(data, dict):
            return {k: self.scrub_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.scrub_data(v) for v in data]
        else:
            # convert other types (int, float, bool, None) to string for scrubbing
            return self.scrub(str(data))
