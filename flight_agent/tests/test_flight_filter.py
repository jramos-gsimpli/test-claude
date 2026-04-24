import pytest
from src.flight_filter import FlightFilter


PRICE_THRESHOLD = 870.0


class TestFlightFilter:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.filter = FlightFilter(PRICE_THRESHOLD)

    def _make_flight(self, price: float, destination: str = "MAD") -> dict:
        return {
            "id": f"flight_{destination}",
            "origin": "EZE",
            "destination": destination,
            "departure_at": "2024-06-01T10:00:00",
            "price": price,
            "currency": "USD",
            "airline": "IB",
            "stops": 1,
        }

    def test_keeps_flight_below_threshold(self):
        result = self.filter.filter_by_price([self._make_flight(500.00)])

        assert len(result) == 1

    def test_keeps_flight_at_exact_threshold(self):
        result = self.filter.filter_by_price([self._make_flight(870.00)])

        assert len(result) == 1

    def test_excludes_flight_one_cent_above_threshold(self):
        result = self.filter.filter_by_price([self._make_flight(870.01)])

        assert result == []

    def test_excludes_flight_well_above_threshold(self):
        result = self.filter.filter_by_price([self._make_flight(1200.00)])

        assert result == []

    def test_returns_empty_list_when_input_is_empty(self):
        result = self.filter.filter_by_price([])

        assert result == []

    def test_filters_mixed_price_list_correctly(self):
        flights = [
            self._make_flight(600.00, "MAD"),
            self._make_flight(900.00, "LHR"),
            self._make_flight(870.00, "CDG"),
            self._make_flight(1200.00, "FRA"),
            self._make_flight(750.00, "BCN"),
        ]

        result = self.filter.filter_by_price(flights)

        assert len(result) == 3
        destinations = {f["destination"] for f in result}
        assert destinations == {"MAD", "CDG", "BCN"}

    def test_preserves_all_flight_fields_unchanged(self):
        original = self._make_flight(500.00)

        result = self.filter.filter_by_price([original])

        assert result[0] == original

    def test_respects_custom_threshold(self):
        strict_filter = FlightFilter(max_price=600.0)
        flights = [
            self._make_flight(500.00, "MAD"),
            self._make_flight(750.00, "LHR"),
        ]

        result = strict_filter.filter_by_price(flights)

        assert len(result) == 1
        assert result[0]["destination"] == "MAD"
