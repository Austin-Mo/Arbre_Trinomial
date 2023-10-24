class Market:
    def __init__(self, volatility, risk_free_rate, spot, dividends):
        self.vol = volatility
        self.rate = risk_free_rate
        self.spot = spot
        self.div = dividends

    def param(self):
        print(f"MARKET - Volatilité: {self.vol}, Taux: {self.rate}, Spot: {self.spot}, Dividendes: {self.div}")
