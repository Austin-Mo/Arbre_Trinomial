from math import *


class Node:
    def __init__(self, spot, p_transition):
        self.spot = spot
        self.next_up = None
        self.next_mid = None
        self.next_down = None
        self.node_up = None
        self.node_down = None
        self.p_up = None
        self.p_mid = None
        self.p_down = None
        self.p_transition = p_transition
        self.pr_opt = None

    def forward(self, market, model):
        fwd_price = self.spot * exp(market.rate * model.t_step)
        return fwd_price

    def variance(self, market, model):
        var = self.spot ** 2 * exp(2 * market.rate * model.t_step) * (exp(market.vol ** 2 * model.t_step) - 1)
        return var

    def calculate_proba(self, alpha, market, model, dividend):
        var = self.variance(market, model)
        spot = self.next_mid.spot
        esp = Node.forward(self, market, model) - dividend
        self.p_down = (spot ** (-2) * (var + esp ** 2) - 1 - (alpha + 1) *
                       (spot ** (-1) * esp - 1)) / ((1 - alpha) * (alpha ** (-2) - 1))
        self.p_up = (spot ** (-1) * esp - 1 - (alpha ** (-1) - 1) * self.p_down) / (alpha - 1)
        self.p_mid = 1 - (self.p_down + self.p_up)
        self.set_total_probabilities()
        if self.p_down < 0 or self.p_mid < 0 or self.p_up < 0:
            raise ValueError("Error, negative probability with node " + str(self) + " !")

    def set_total_probabilities(self):
        self.next_down.p_transition += self.p_transition * self.p_down
        self.next_mid.p_transition += self.p_transition * self.p_mid
        self.next_up.p_transition += self.p_transition * self.p_up

    def price(self, option, tree):
        df = tree.discount_factor()
        if self.next_mid is None:
            self.pr_opt = option.payoff(self.spot)
        elif self.pr_opt is None:
            if self.next_up is None:
                self.pr_opt = df * self.next_mid.price(option, tree)
                if option.type == 'US':
                    self.pr_opt = max(self.pr_opt, option.payoff(self.spot))
            else:
                self.pr_opt = df * (self.p_up * self.next_up.price(option, tree) +
                                    self.p_mid * self.next_mid.price(option, tree) +
                                    self.p_down * self.next_down.price(option, tree))
                if option.type == 'US':
                    self.pr_opt = max(self.pr_opt, option.payoff(self.spot))
        return self.pr_opt

    @staticmethod
    def associate_up_down(up_node, down_node):
        up_node.node_down = down_node
        down_node.node_up = up_node


















