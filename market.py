from datetime import date


class Market:
    def __init__(self, volatility: float, risk_free_rate: float, spot: float,
                 dividends: dict[date, float]) -> None:
        self.vol = volatility
        self.rate = risk_free_rate
        self.spot = spot
        self.div = dividends

    # Fonction pour retourner les valeurs de l'objet
    def param(self) -> None:
        print(f"MARKET - Volatilité: {self.vol}, Taux: {self.rate}, Spot: {self.spot}, Dividendes: {self.div}")
