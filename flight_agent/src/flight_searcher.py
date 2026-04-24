from typing import Any, Dict, List, Optional


class FlightSearchError(Exception):
    pass


class FlightSearcher:
    def __init__(self, client):
        self._client = client

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        max_price: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        try:
            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": 1,
                "currencyCode": "USD",
            }
            if max_price is not None:
                params["maxPrice"] = max_price

            response = self._client.shopping.flight_offers_search.get(**params)
            return self._parse_response(response.data)
        except Exception as e:
            raise FlightSearchError(
                f"Error searching {origin}→{destination}: {e}"
            ) from e

    def _parse_response(self, data: List[Dict]) -> List[Dict[str, Any]]:
        return [
            {
                "id": offer["id"],
                "origin": offer["itineraries"][0]["segments"][0]["departure"]["iataCode"],
                "destination": offer["itineraries"][0]["segments"][-1]["arrival"]["iataCode"],
                "departure_at": offer["itineraries"][0]["segments"][0]["departure"]["at"],
                "price": float(offer["price"]["total"]),
                "currency": offer["price"]["currency"],
                "airline": offer["validatingAirlineCodes"][0],
                "stops": len(offer["itineraries"][0]["segments"]) - 1,
            }
            for offer in data
        ]
