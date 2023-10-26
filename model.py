from datetime import datetime


class Model:
    def __init__(self, option_maturity, pricing_date, steps_number):
        self.maturity = option_maturity
        self.pr_date = pricing_date.date()
        self.steps_nb = steps_number
        self.t_step = self.calculate_t_step()

    def calculate_t_step(self):
        return (self.maturity - self.pr_date).days / self.steps_nb / 365  # t_step en année

    def param(self):
        print(f"MODEL - Pricing Date: {self.pr_date}, Nombre de pas: {self.steps_nb}, T_step: {self.t_step}")
