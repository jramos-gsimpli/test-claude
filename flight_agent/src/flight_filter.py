from typing import Any, Dict, List


class FlightFilter:
    def __init__(self, max_price: float):
        self._max_price = max_price

    def filter_by_price(self, flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [f for f in flights if f["price"] <= self._max_price]
