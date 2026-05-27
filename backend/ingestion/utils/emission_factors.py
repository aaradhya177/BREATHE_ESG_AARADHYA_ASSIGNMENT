from decimal import Decimal


DEFRA_2023_TRAVEL_FACTORS = {
    "flight_economy": {
        "factor": Decimal("0.146"),
        "unit": "kgCO2e/passenger-km",
        "label": "DEFRA 2023 air passenger-km economy approximate",
    },
    "flight_business": {
        "factor": Decimal("0.434"),
        "unit": "kgCO2e/passenger-km",
        "label": "DEFRA 2023 air passenger-km business approximate",
    },
    "flight_first": {
        "factor": Decimal("0.579"),
        "unit": "kgCO2e/passenger-km",
        "label": "DEFRA 2023 air passenger-km first approximate",
    },
    "hotel_stay": {
        "factor": Decimal("15.0"),
        "unit": "kgCO2e/night",
        "label": "DEFRA 2023 hotel night approximate",
    },
    "car_rental": {
        "factor": Decimal("0.171"),
        "unit": "kgCO2e/km",
        "label": "DEFRA 2023 average car km approximate",
    },
    "rail_travel": {
        "factor": Decimal("0.035"),
        "unit": "kgCO2e/passenger-km",
        "label": "DEFRA 2023 rail passenger-km approximate",
    },
}
