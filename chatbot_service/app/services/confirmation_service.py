class ConfirmationService:
    def quick_confirm(self, message: str) -> str | None:
        normalized = message.lower().strip()

        confirm_phrases = {
            "yes",
            "y",
            "yeah",
            "yep",
            "sure",
            "confirm",
            "update it",
            "do it",
            "yes update it",
        }

        reject_phrases = {
            "no",
            "n",
            "nope",
            "don't",
            "do not",
            "keep it",
            "keep the old one",
            "don't update",
            "do not update",
        }

        if normalized in confirm_phrases:
            return "confirm"

        if normalized in reject_phrases:
            return "reject"

        return None


confirmation_service = ConfirmationService()