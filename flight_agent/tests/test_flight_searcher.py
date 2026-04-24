import pytest
from unittest.mock import MagicMock
from src.flight_searcher import FlightSearcher, FlightSearchError


class TestFlightSearcher:
    @pytest.fixture(autouse=True)
    def setup(self, mock_amadeus_client, sample_amadeus_offer):
        self.mock_client = mock_amadeus_client
        self.offer = sample_amadeus_offer
        self.searcher = FlightSearcher(self.mock_client)

    def _set_api_response(self, data):
        self.mock_client.shopping.flight_offers_search.get.return_value = MagicMock(data=data)

    def test_calls_api_with_required_params(self):
        self._set_api_response([])

        self.searcher.search_flights("BUE", "MAD", "2024-06-01")

        self.mock_client.shopping.flight_offers_search.get.assert_called_once_with(
            originLocationCode="BUE",
            destinationLocationCode="MAD",
            departureDate="2024-06-01",
            adults=1,
            currencyCode="USD",
        )

    def test_includes_max_price_param_when_provided(self):
        self._set_api_response([])

        self.searcher.search_flights("BUE", "MAD", "2024-06-01", max_price=870)

        kwargs = self.mock_client.shopping.flight_offers_search.get.call_args[1]
        assert kwargs["maxPrice"] == 870

    def test_omits_max_price_param_when_not_provided(self):
        self._set_api_response([])

        self.searcher.search_flights("BUE", "MAD", "2024-06-01")

        kwargs = self.mock_client.shopping.flight_offers_search.get.call_args[1]
        assert "maxPrice" not in kwargs

    def test_returns_parsed_flight_data(self):
        self._set_api_response([self.offer])

        result = self.searcher.search_flights("BUE", "MAD", "2024-06-01")

        assert len(result) == 1
        flight = result[0]
        assert flight["id"] == "offer_001"
        assert flight["origin"] == "EZE"
        assert flight["destination"] == "MAD"
        assert flight["departure_at"] == "2024-06-01T10:00:00"
        assert flight["price"] == 750.0
        assert flight["currency"] == "USD"
        assert flight["airline"] == "IB"
        assert flight["stops"] == 0

    def test_returns_empty_list_when_api_returns_no_results(self):
        self._set_api_response([])

        result = self.searcher.search_flights("BUE", "MAD", "2024-06-01")

        assert result == []

    def test_counts_stops_correctly_for_connecting_flight(self):
        offer_with_connection = {
            **self.offer,
            "itineraries": [
                {
                    "segments": [
                        {
                            "departure": {"iataCode": "EZE", "at": "2024-06-01T10:00:00"},
                            "arrival": {"iataCode": "GRU", "at": "2024-06-01T12:00:00"},
                        },
                        {
                            "departure": {"iataCode": "GRU", "at": "2024-06-01T15:00:00"},
                            "arrival": {"iataCode": "MAD", "at": "2024-06-02T05:00:00"},
                        },
                    ]
                }
            ],
        }
        self._set_api_response([offer_with_connection])

        result = self.searcher.search_flights("BUE", "MAD", "2024-06-01")

        assert result[0]["stops"] == 1

    def test_uses_last_segment_arrival_as_destination(self):
        offer_with_connection = {
            **self.offer,
            "itineraries": [
                {
                    "segments": [
                        {
                            "departure": {"iataCode": "EZE", "at": "2024-06-01T10:00:00"},
                            "arrival": {"iataCode": "GRU", "at": "2024-06-01T12:00:00"},
                        },
                        {
                            "departure": {"iataCode": "GRU", "at": "2024-06-01T15:00:00"},
                            "arrival": {"iataCode": "MAD", "at": "2024-06-02T05:00:00"},
                        },
                    ]
                }
            ],
        }
        self._set_api_response([offer_with_connection])

        result = self.searcher.search_flights("BUE", "MAD", "2024-06-01")

        assert result[0]["destination"] == "MAD"

    def test_raises_flight_search_error_on_api_failure(self):
        self.mock_client.shopping.flight_offers_search.get.side_effect = Exception("Connection timeout")

        with pytest.raises(FlightSearchError, match="Connection timeout"):
            self.searcher.search_flights("BUE", "MAD", "2024-06-01")

    def test_wraps_original_exception_as_cause(self):
        original = Exception("Original error")
        self.mock_client.shopping.flight_offers_search.get.side_effect = original

        with pytest.raises(FlightSearchError) as exc_info:
            self.searcher.search_flights("BUE", "MAD", "2024-06-01")

        assert exc_info.value.__cause__ is original

    def test_parses_multiple_offers(self):
        second_offer = {
            **self.offer,
            "id": "offer_002",
            "price": {"total": "820.00", "currency": "USD"},
        }
        self._set_api_response([self.offer, second_offer])

        result = self.searcher.search_flights("BUE", "MAD", "2024-06-01")

        assert len(result) == 2
        assert result[1]["price"] == 820.0
