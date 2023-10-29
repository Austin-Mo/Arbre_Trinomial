from math import *
from market import Market
from model import Model
from option import Option


class Node:
    def __init__(self, spot: float, p_transition: float) -> None:
        self.spot: float = spot
        self.next_up: 'Optional[Node]' = None
        self.next_mid: 'Optional[Node]' = None
        self.next_down: 'Optional[Node]' = None
        self.node_up: 'Optional[Node]' = None
        self.node_down: 'Optional[Node]' = None
        self.p_up: 'Optional[float]' = None
        self.p_mid: 'Optional[float]' = None
        self.p_down: 'Optional[float]' = None
        self.p_transition: float = p_transition
        self.pr_opt: 'Optional[float]' = None

    # Calcul du forward
    def forward(self, market: Market, model: Model) -> float:
        return self.spot * exp(market.rate * model.t_step)

    # Calcul de la variance
    def variance(self, market: Market, model: Model) -> float:
        return self.spot ** 2 * exp(2 * market.rate * model.t_step) * (exp(market.vol ** 2 * model.t_step) - 1)

    # Calcul des probabilités
    def calculate_proba(self, alpha: float, market: Market, model: Model, dividend: float) -> None:
        var = self.variance(market, model)
        spot = self.next_mid.spot
        esp = Node.forward(self, market, model) - dividend
        self.p_down = (spot ** (-2) * (var + esp ** 2) - 1 - (alpha + 1) *
                       (spot ** (-1) * esp - 1)) / ((1 - alpha) * (alpha ** (-2) - 1))
        self.p_up = (spot ** (-1) * esp - 1 - (alpha ** (-1) - 1) * self.p_down) / (alpha - 1)
        self.p_mid = 1 - (self.p_down + self.p_up)
        self.set_total_probabilities()
        # Erreur si proba négatives
        if self.p_down < 0 or self.p_mid < 0 or self.p_up < 0:
            raise ValueError(f"Error, negative probability with node {self} !")

    # Probabilité totales
    def set_total_probabilities(self) -> None:
        self.next_down.p_transition += self.p_transition * self.p_down
        self.next_mid.p_transition += self.p_transition * self.p_mid
        self.next_up.p_transition += self.p_transition * self.p_up

    # Calcul du prix (récursif)
    def price(self, option: Option, tree: 'Tree') -> float:
        df = tree.discount_factor()  # Récupération de l'arbre
        if self.next_mid is None:  # Aller jusqu'à la fin de l'arbre
            self.pr_opt = option.payoff(self.spot)  # Calcul du payoff du noeud
        elif self.pr_opt is None:  # Si le nœud n'a pas de prix et n'est pas le dernier nœud de l'arbre
            if self.next_up is None:  # Si le nœud n'a pas de next_up
                self.pr_opt = df * self.next_mid.price(option, tree)  # Calculer le prix discounté avec son next_mid
                if option.type == 'US':  # Et si c'est une option américaine
                    self.pr_opt = max(self.pr_opt, option.payoff(self.spot))  # Prendre le max entre la valeur de continuation ou la valeur d'exercice immédiat
            else:  # Sinon calcul du prix en fonction des prix suivant pondérés par les probas
                self.pr_opt = df * (self.p_up * self.next_up.price(option, tree) +
                                    self.p_mid * self.next_mid.price(option, tree) +
                                    self.p_down * self.next_down.price(option, tree))
                if option.type == 'US':
                    self.pr_opt = max(self.pr_opt, option.payoff(self.spot))
        return self.pr_opt

    # Méthode pour associer 2 noeuds up/down
    @staticmethod
    def associate_up_down(up_node: 'Node', down_node: 'Node') -> None:
        up_node.node_down = down_node
        down_node.node_up = up_node
