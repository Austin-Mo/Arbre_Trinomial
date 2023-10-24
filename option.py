from datetime import datetime


class Option:
    def __init__(self, strike, maturity_date, option_type, option_style):
        self.K = strike
        self.maturity = datetime.strptime(maturity_date, "%d/%m/%Y").date()
        if option_type not in ["Call", "Put"]:
            raise ValueError(f"Invalid option type: {option_type}")
        self.call_put = option_type
        if option_style not in ["EU", "US"]:
            raise ValueError(f"Invalid option style: {option_style}")
        self.type = option_style

    def payoff(self, spot):
        if self.call_put == "Call":
            return max(spot - self.K, 0)
        elif self.call_put == "Put":
            return max(self.K - spot, 0)
        else:
            raise ValueError("Unknown option type")

    def param(self):
        print(f"OPTION - Strike: {self.K}, Maturité: {self.maturity}, Type: {self.call_put}, Type: {self.type}")
