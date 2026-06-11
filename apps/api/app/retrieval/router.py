class EvidenceRouter:
    """Routes questions to evidence-specific retrievers."""

    def route(self, question: str) -> list[str]:
        lowered = question.lower()
        routes: list[str] = ["text"]
        if "table" in lowered or "row" in lowered or "column" in lowered:
            routes.append("table")
        if "figure" in lowered or "chart" in lowered or "diagram" in lowered:
            routes.append("figure")
        if "equation" in lowered or "formula" in lowered:
            routes.append("equation")
        return sorted(set(routes))
