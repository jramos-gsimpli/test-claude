import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, call
from src.agent import FlightAgent
from src.flight_searcher import FlightSearchError
from src import config


class TestFlightAgent:
    @pytest.fixture(autouse=True)
    def setup(self, sample_flight):
        self.mock_searcher = MagicMock()
        self.mock_filter = MagicMock()
        self.mock_notifier = MagicMock()
        self.agent = FlightAgent(self.mock_searcher, self.mock_filter, self.mock_notifier)
        self.sample_flight = sample_flight

    def _configure_mocks(self, searcher_returns=None, filter_returns=None):
        self.mock_searcher.search_flights.return_value = searcher_returns or []
        self.mock_filter.filter_by_price.return_value = filter_returns or []

    def test_searches_every_configured_european_destination(self):
        self._configure_mocks()

        self.agent.run()

        assert self.mock_searcher.search_flights.call_count == len(config.EUROPEAN_AIRPORTS)

    def test_searches_each_destination_only_once(self):
        self._configure_mocks()

        self.agent.run()

        searched_destinations = [
            call_args[0][1]
            for call_args in self.mock_searcher.search_flights.call_args_list
        ]
        assert len(searched_destinations) == len(set(searched_destinations))

    def test_always_uses_buenos_aires_as_origin(self):
        self._configure_mocks()

        self.agent.run()

        for call_args in self.mock_searcher.search_flights.call_args_list:
            assert call_args[0][0] == config.ORIGIN_AIRPORT

    def test_passes_price_threshold_to_searcher(self):
        self._configure_mocks()

        self.agent.run()

        for call_args in self.mock_searcher.search_flights.call_args_list:
            assert call_args[1]["max_price"] == config.PRICE_THRESHOLD

    def test_searches_correct_departure_date(self):
        self._configure_mocks()
        expected_date = (date.today() + timedelta(days=config.SEARCH_DAYS_AHEAD)).isoformat()

        self.agent.run()

        for call_args in self.mock_searcher.search_flights.call_args_list:
            assert call_args[0][2] == expected_date

    def test_applies_price_filter_to_each_search_result(self):
        self.mock_searcher.search_flights.return_value = [self.sample_flight]
        self.mock_filter.filter_by_price.return_value = []

        self.agent.run()

        assert self.mock_filter.filter_by_price.call_count == len(config.EUROPEAN_AIRPORTS)

    def test_sends_notification_when_affordable_flights_found(self):
        self._configure_mocks(
            searcher_returns=[self.sample_flight],
            filter_returns=[self.sample_flight],
        )

        self.agent.run()

        self.mock_notifier.send_notification.assert_called_once()
        call_args = self.mock_notifier.send_notification.call_args[0]
        assert call_args[0] == config.RECIPIENT_EMAIL
        assert len(call_args[1]) > 0

    def test_sends_notification_to_configured_recipient(self):
        self._configure_mocks(
            searcher_returns=[self.sample_flight],
            filter_returns=[self.sample_flight],
        )

        self.agent.run()

        call_args = self.mock_notifier.send_notification.call_args[0]
        assert call_args[0] == config.RECIPIENT_EMAIL

    def test_does_not_send_notification_when_no_affordable_flights(self):
        self._configure_mocks(
            searcher_returns=[self.sample_flight],
            filter_returns=[],
        )

        self.agent.run()

        self.mock_notifier.send_notification.assert_not_called()

    def test_does_not_send_notification_when_all_searches_return_empty(self):
        self._configure_mocks(searcher_returns=[], filter_returns=[])

        self.agent.run()

        self.mock_notifier.send_notification.assert_not_called()

    def test_continues_searching_after_one_destination_fails(self):
        self.mock_searcher.search_flights.side_effect = FlightSearchError("API error")
        self.mock_filter.filter_by_price.return_value = []

        self.agent.run()

        assert self.mock_searcher.search_flights.call_count == len(config.EUROPEAN_AIRPORTS)

    def test_skips_failed_destination_without_crashing(self):
        def searcher_side_effect(origin, dest, departure_date, **kwargs):
            if dest == config.EUROPEAN_AIRPORTS[0]:
                raise FlightSearchError("API error")
            return [self.sample_flight]

        self.mock_searcher.search_flights.side_effect = searcher_side_effect
        self.mock_filter.filter_by_price.return_value = [self.sample_flight]

        result = self.agent.run()

        assert len(result) == len(config.EUROPEAN_AIRPORTS) - 1

    def test_returns_all_affordable_flights_found(self):
        self._configure_mocks(
            searcher_returns=[self.sample_flight],
            filter_returns=[self.sample_flight],
        )

        result = self.agent.run()

        assert len(result) == len(config.EUROPEAN_AIRPORTS)

    def test_returns_empty_list_when_nothing_affordable(self):
        self._configure_mocks(filter_returns=[])

        result = self.agent.run()

        assert result == []

    def test_aggregates_flights_from_multiple_destinations(self):
        madrid_flight = {**self.sample_flight, "destination": "MAD"}
        london_flight = {**self.sample_flight, "destination": "LHR", "price": 800.0}

        def filter_side_effect(flights):
            return flights

        def searcher_side_effect(origin, dest, date, **kwargs):
            if dest == "MAD":
                return [madrid_flight]
            if dest == "LHR":
                return [london_flight]
            return []

        self.mock_searcher.search_flights.side_effect = searcher_side_effect
        self.mock_filter.filter_by_price.side_effect = filter_side_effect

        result = self.agent.run()

        destinations_found = {f["destination"] for f in result}
        assert "MAD" in destinations_found
        assert "LHR" in destinations_found
