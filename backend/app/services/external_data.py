# Simulation of external API calls (Weather, Marine Traffic, etc.)
import random
from datetime import datetime, timedelta

class ExternalDataService:
    def __init__(self):
        pass

    def check_weather_alert(self, route_or_port: str):
        """
        Returns a mock weather alert if any.
        """
        # 20% chance of bad weather
        if random.random() < 0.2:
            return {
                "type": "WEATHER",
                "severity": "HIGH",
                "message": f"Storm detected near {route_or_port}. Potential delay of 2-3 days.",
                "impact_days": 3
            }
        return None

    def check_port_congestion(self, port: str):
        """
        Returns congestion delay in days.
        """
        congestion_map = {
            "CNSHA": 5, # Shanghai
            "USLAX": 7, # Los Angeles
            "BEANR": 2, # Antwerp
            "FRLEH": 1  # Le Havre
        }
        # Fuzzy match
        for key, days in congestion_map.items():
            if key in port.upper() or port.upper() in key:
                return days
        return 0

    def get_market_rate_index(self, mode: str, origin: str, dest: str):
        """
        Returns a mock freight index trend.
        """
        base_rate = 1500 if mode == "SEA" else 4000
        trend = random.choice(["UP", "DOWN", "STABLE"])
        return {
            "rate": base_rate * (1 + random.uniform(-0.1, 0.2)),
            "currency": "USD",
            "trend": trend
        }

    def get_flight_status(self, flight_number: str):
        """
        Mock flight status.
        """
        return random.choice(["ON_TIME", "DELAYED", "CANCELLED"])

external_service = ExternalDataService()
