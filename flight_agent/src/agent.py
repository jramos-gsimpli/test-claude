from datetime import date, timedelta
from typing import Any, Dict, List

from . import config
from .email_notifier import EmailNotifier
from .flight_filter import FlightFilter
from .flight_searcher import FlightSearchError, FlightSearcher


class FlightAgent:
    def __init__(
        self,
        searcher: FlightSearcher,
        flight_filter: FlightFilter,
        notifier: EmailNotifier,
    ):
        self._searcher = searcher
        self._filter = flight_filter
        self._notifier = notifier

    def run(self) -> List[Dict[str, Any]]:
        departure_date = (
            date.today() + timedelta(days=config.SEARCH_DAYS_AHEAD)
        ).isoformat()
        affordable_flights = self._search_all_destinations(departure_date)
        if affordable_flights:
            self._notifier.send_notification(config.RECIPIENT_EMAIL, affordable_flights)
        return affordable_flights

    def _search_all_destinations(self, departure_date: str) -> List[Dict[str, Any]]:
        all_affordable: List[Dict[str, Any]] = []
        for destination in config.EUROPEAN_AIRPORTS:
            try:
                flights = self._searcher.search_flights(
                    config.ORIGIN_AIRPORT,
                    destination,
                    departure_date,
                    max_price=config.PRICE_THRESHOLD,
                )
                affordable = self._filter.filter_by_price(flights)
                all_affordable.extend(affordable)
            except FlightSearchError:
                continue
        return all_affordable
