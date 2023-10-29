from datetime import datetime


class Option:
    def __init__(self, strike: float, maturity_date: datetime, option_type: str, option_style: str):
        self.K = strike
        self.maturity = maturity_date.date()
        if option_type not in ["Call", "Put"]:
            raise ValueError(f"Invalid option type: {option_type}")
        self.call_put = option_type
        if option_style not in ["EU", "US"]:
            raise ValueError(f"Invalid option style: {option_style}")
        self.type = option_style

    # Formules des Call / Put
    def payoff(self, spot: float) -> float:
        if self.call_put == "Call":
            return max(spot - self.K, 0)
        elif self.call_put == "Put":
            return max(self.K - spot, 0)
        else:
            raise ValueError("Unknown option type")

    # Fonction pour retourner les valeurs de l'objet
    def param(self) -> None:
        print(f"OPTION - Strike: {self.K}, Maturité: {self.maturity}, Type: {self.call_put}, Type: {self.type}")
