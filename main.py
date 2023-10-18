# Creation Arbre


from math import *
from datetime import datetime, date

# Import et début start du temps d'exécution
import time
start_time = time.time()

# Changer la profondeur de la récursivité
import sys
sys.setrecursionlimit(100000)

class Market:
    def __init__(self, volatility, risk_free_rate, spot, dividends):
        self.vol = volatility
        self.rate = risk_free_rate
        self.spot = spot
        self.div = dividends

    def parametres(self):
        return self.vol, self.rate, self.spot, self.spot, self.div


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

    def parametres(self):
        return self.K, self.maturity, self.call_put, self.type


class Model:
    def __init__(self, option, pricing_date, steps_number):
        self.option = option
        self.pr_date = datetime.strptime(pricing_date, "%d/%m/%Y").date()
        self.steps_nb = steps_number
        self.t_step = (option.maturity - self.pr_date).days / self.steps_nb / 365  # t_step en année

    def parametres(self):
        return self.pr_date, self.steps_nb, self.t_step


class Node:
    def __init__(self, spot):
        self.spot = spot
        self.next_up = None
        self.next_mid = None
        self.next_down = None
        self.node_up = None
        self.node_down = None
        self.p_up = None
        self.p_mid = None
        self.p_down = None
        self.pr_opt = None

    def forward(self, market, model):        # t_step ?
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
                  (spot **(-1) * esp - 1)) / ((1 - alpha) * (alpha ** (-2) - 1))
        self.p_up = (spot ** (-1) * esp - 1 - (alpha ** (-1) - 1) * self.p_down) / (alpha - 1)
        self.p_mid = 1 - (self.p_down + self.p_up)

    def price(self, option):
        df = tree.discount_factor()
        if self.next_mid is None:
            self.pr_opt = option.payoff(self.spot)
        elif self.pr_opt is None:
            self.pr_opt = df * (self.p_up * self.next_up.price(option) +
                                self.p_mid * self.next_mid.price(option) +
                                self.p_down * self.next_down.price(option))
            if option.type == 'US':
                self.pr_opt = max(self.pr_opt, option.payoff(self.spot))
        return self.pr_opt

    @staticmethod
    def associate_up_down(up_node, down_node):
        up_node.node_down = down_node
        down_node.node_up = up_node


class NodeCreation:
    def __init__(self, tree_alpha):
        self.tree_alpha = tree_alpha
        self.check_node = None
        self.current_node = None
        self.fwd_price = None
        self.code_dict = {
            (1, "up"): lambda: self.up_and_close(),
            (2, "up"): lambda: self.up_and_above(),
            (0, "up"): lambda: self.up_and_bellow(),
            (1, "down"): lambda: self.down_and_close(),
            (2, "down"): lambda: self.down_and_above(),
            (0, "down"): lambda: self.down_and_bellow(),
        }

    def create_next_nodes(self, root_node, market, model, dividend):
        self.create_first_nodes(root_node, market, model, dividend)  # création des 3 premiers noeuds
        self.create_nodes(root_node, market, model, dividend, direction='up')  # création des noeuds du dessus
        self.create_nodes(root_node, market, model, dividend, direction='down')  # création des noeuds du dessous

    def create_first_nodes(self, root_node, market, model, dividend):
        # Calculer le prix forward pour le noeud actuel.
        self.fwd_price = root_node.forward(market, model) - dividend

        # Créer les trois noeuds suivants pour up, mid, et down.
        root_node.next_up = Node(self.fwd_price * self.tree_alpha)
        root_node.next_mid = Node(self.fwd_price)
        root_node.next_down = Node(self.fwd_price / self.tree_alpha)

        # Lier les noeuds up et down des noeuds crées
        Node.associate_up_down(root_node.next_up, root_node.next_mid)
        Node.associate_up_down(root_node.next_mid, root_node.next_down)
        Node.calculate_proba(root_node, self.tree_alpha, market, model, dividend)

    def create_nodes(self, node, market, model, dividend, direction='up'):
        self.current_node = node
        next_direction = "next_" + direction
        node_direction = "node_" + direction

        # Boucle pour parcourir tous les noeuds au dessus/dessous par rapport au noeud entré (noeud root)
        while getattr(self.current_node, node_direction) is not None:
            self.check_node = getattr(self.current_node, next_direction)
            self.current_node = getattr(self.current_node, node_direction)
            self.fwd_price = max(self.current_node.forward(market, model) - dividend, 0.01)
            check = self.is_close(self.check_node, self.fwd_price)
            # Use the dictionary to execute the appropriate code block
            key = (check, direction)
            if key in self.code_dict:
                self.code_dict[key]()  # Execute the corresponding code block
            self.current_node.calculate_proba(self.tree_alpha, market, model, dividend)  # Calculer les probas du noeud sur lequel on travaille

    @staticmethod
    def is_close(node, fwd_price):  # Modifier les fonctions pour les mettre dans NODE ?
        up_price = node.spot * ((1 + tree.alpha) / 2)
        down_price = node.spot * ((1 + 1 / tree.alpha) / 2)
        if fwd_price < down_price:
            return 0
        elif fwd_price > up_price:
            return 2
        else:
            return 1

    def up_and_close(self):
        new_node = Node(self.check_node.spot * self.tree_alpha)  # Création d'un nouveau noeud
        self.current_node.next_up = new_node  # Associer le next_up au nouveau noeud
        self.current_node.next_mid = self.check_node
        self.current_node.next_down = self.check_node.node_down
        Node.associate_up_down(new_node, self.check_node)  # Associer les up/down des noeuds,

    def up_and_above(self):
        current_node_node_down_next_up = self.check_node
        while self.is_close(self.check_node, self.fwd_price) == 2:
            new_down = self.check_node
            self.check_node = Node(self.check_node.spot*self.tree_alpha)
        Node.associate_up_down(self.check_node, new_down)
        if new_down != current_node_node_down_next_up:
            Node.associate_up_down(new_down, current_node_node_down_next_up)
        self.up_and_close()

    def up_and_bellow(self):
        self.check_node = self.check_node.node_down
        self.up_and_close()

    def down_and_close(self):
        new_node = Node(self.check_node.spot / self.tree_alpha)  # Création d'un nouveau noeud
        self.current_node.next_down = new_node  # Associer le next_up au nouveau noeud
        self.current_node.next_mid = self.check_node
        self.current_node.next_up = self.check_node.node_up
        Node.associate_up_down(self.check_node, new_node)  # Associer les up/down des noeuds,

    def down_and_bellow(self):
        current_node_node_up_next_down = self.check_node
        while self.is_close(self.check_node, self.fwd_price) == 0:
            new_up = self.check_node
            self.check_node = Node(self.check_node.spot/self.tree_alpha)
        Node.associate_up_down(new_up, self.check_node)
        if new_up != current_node_node_up_next_down:
            Node.associate_up_down(current_node_node_up_next_down, new_up)
        self.down_and_close()

    def down_and_above(self):
        self.check_node = self.check_node.node_up
        self.down_and_close()


class Tree:
    def __init__(self, model, market, option):
        self.model = model
        self.div_steps = self.convert_dates_to_steps(market.div, model.pr_date, model.steps_nb)
        self.market = market
        self.option = option
        self.alpha = self.calculate_alpha()
        self.NodeCreation = NodeCreation(self.alpha)

    def convert_dates_to_steps(self, dividend_dict, reference_date, steps_number):
        return {self.date_to_annual_time_measure(date, reference_date, steps_number): amount for date, amount in
                dividend_dict.items()}

    def date_to_annual_time_measure(self, dividend_date, reference_date, steps_number):
        return (dividend_date - reference_date).days / 365

    def calculate_alpha(self):
        alpha = exp(market.vol * sqrt(3 * model.t_step))
        return alpha

    def create_tree(self, root):
        for i in range(model.steps_nb):
            # Creation des noeuds suivants
            dividend = 0
            for key_step in self.div_steps.keys():
                if (i + 1) * model.t_step >= key_step > i * model.t_step:  # step+1 ?
                    dividend += self.div_steps[key_step]  # créer un dictionnaire avec des dates correspondant à une étape

            self.NodeCreation.create_next_nodes(root, market, model, dividend)
            root = root.next_mid

    def discount_factor(self):
        return exp(-self.market.rate * self.model.t_step)


# main
if __name__ == '__main__':
    # Ajout des paramètres
    option = Option(strike=102, maturity_date="01/07/2024", option_type="Call", option_style="EU")
    model = Model(option, pricing_date="01/09/2023", steps_number=2000)
    div = {date(2024, 3, 1): 5, date(2024, 4, 1): 3}
    #div = {}

    market = Market(volatility=0.25, risk_free_rate=0.02, spot=100, dividends=div)

    print('Market: ' + str(market.parametres()))
    print('Option: ' + str(option.parametres()))
    print('Model: ' + str(model.parametres()))
    # Creation de l'arbre
    tree = Tree(model, market, option)
    print(f"Alpha: {tree.alpha} Times step: {tree.model.t_step} \n")

    # Création du noeud initial
    root = Node(market.spot)
    # Appel de la fonction créer arbre
    tree.create_tree(root)

    #Node.display_all_nodes()

    print("\nLe prix de l'option est: " + str(root.price(option)))

    # Tester le temps d'exécution
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Temps écoulé: {elapsed_time:.5f} secondes")
