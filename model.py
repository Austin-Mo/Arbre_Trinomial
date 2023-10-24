from datetime import datetime


class Model:
    def __init__(self, option, pricing_date, steps_number):
        self.option = option
        self.pr_date = datetime.strptime(pricing_date, "%d/%m/%Y").date()
        self.steps_nb = steps_number
        self.t_step = (option.maturity - self.pr_date).days / self.steps_nb / 365  # t_step en année

    def param(self):
        print(f"MODEL - Pricing Date: {self.pr_date}, Nombre de pas: {self.steps_nb}, T_step: {self.t_step}")
