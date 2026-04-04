from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Abstract base for all data source scrapers."""

    @abstractmethod
    async def scrape(self, params: dict) -> dict:
        """
        Perform the search and return structured findings.

        Always returns a dict with at least:
          - "status": "ok" | "no_results" | "unavailable"
          - "source": human-readable name of the data source
          - "results": list of finding dicts (empty list if no results)

        Never raises — catch all exceptions and return status="unavailable".
        """
        ...

    def _unavailable(self, source: str, reason: str) -> dict:
        return {"status": "unavailable", "source": source, "reason": reason, "results": []}

    def _no_results(self, source: str) -> dict:
        return {"status": "no_results", "source": source, "results": []}

    def _ok(self, source: str, results: list) -> dict:
        return {"status": "ok", "source": source, "results": results}
