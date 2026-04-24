import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_amadeus_client():
    return MagicMock()


@pytest.fixture
def sample_amadeus_offer():
    return {
        "id": "offer_001",
        "itineraries": [
            {
                "segments": [
                    {
                        "departure": {"iataCode": "EZE", "at": "2024-06-01T10:00:00"},
                        "arrival": {"iataCode": "MAD", "at": "2024-06-02T05:00:00"},
                    }
                ]
            }
        ],
        "price": {"total": "750.00", "currency": "USD"},
        "validatingAirlineCodes": ["IB"],
    }


@pytest.fixture
def sample_flight():
    return {
        "id": "offer_001",
        "origin": "EZE",
        "destination": "MAD",
        "departure_at": "2024-06-01T10:00:00",
        "price": 750.0,
        "currency": "USD",
        "airline": "IB",
        "stops": 0,
    }
