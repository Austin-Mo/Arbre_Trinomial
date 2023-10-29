from datetime import date, datetime


class Model:
    def __init__(self, option_maturity: date, pricing_date: datetime, steps_number: int) -> None:
        self.maturity = option_maturity
        self.pr_date = pricing_date.date()
        self.steps_nb = steps_number
        self.t_step = self.calculate_t_step()

    # Calcul de t_step en année
    def calculate_t_step(self) -> float:
        return (self.maturity - self.pr_date).days / self.steps_nb / 365

    # Fonction pour retourner les valeurs de l'objet
    def param(self) -> None:
        print(f"MODEL - Pricing Date: {self.pr_date}, Nombre de pas: {self.steps_nb}, T_step: {self.t_step}")
