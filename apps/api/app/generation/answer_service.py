class AnswerService:
    """Assembles grounded prompts and produces citation-constrained answers."""

    def generate(self, question: str, evidence: list[dict]) -> dict:
        raise NotImplementedError("Answer generation is not implemented yet.")
