from amadeus import Client
from dotenv import load_dotenv

from src import config
from src.agent import FlightAgent
from src.email_notifier import EmailNotifier
from src.flight_filter import FlightFilter
from src.flight_searcher import FlightSearcher

load_dotenv()


def main() -> None:
    amadeus_client = Client(
        client_id=config.AMADEUS_CLIENT_ID,
        client_secret=config.AMADEUS_CLIENT_SECRET,
    )

    agent = FlightAgent(
        searcher=FlightSearcher(amadeus_client),
        flight_filter=FlightFilter(config.PRICE_THRESHOLD),
        notifier=EmailNotifier(
            config.SMTP_HOST,
            config.SMTP_PORT,
            config.SMTP_USER,
            config.SMTP_PASSWORD,
        ),
    )

    found = agent.run()
    print(f"Busqueda completada. Se encontraron {len(found)} vuelo(s) accesibles a Europa.")


if __name__ == "__main__":
    main()
