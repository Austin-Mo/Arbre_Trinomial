# Creation Arbre

from math import *
from datetime import datetime, date

# Import et début start du temps d'exécution
import time
start_time = time.time()

# Changer la profondeur de la récursivité
import sys
sys.setrecursionlimit(2000)


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
    all_nodes = []

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

        Node.all_nodes.append(self)

    @classmethod
    def display_all_nodes(cls):
        for node in cls.all_nodes:
            print(node)

    def __repr__(self):
        return str(self.spot)

    def forward(self, market, model, steps_number):
        dividend = 0
        for key_step in market.div.keys():
            if (steps_number+1) >= key_step > steps_number: #step+1 ?
                dividend += market.div[key_step]  # créer un dictionnaire avec des dates correspondant à une étape
        fwd_price = self.spot * exp(market.rate * model.t_step) - dividend
        return fwd_price

    def variance(self, market, model):
        var = self.spot ** 2 * exp(2 * market.rate * model.t_step) * (exp(market.vol ** 2 * model.t_step) - 1)
        return var

    def calculate_proba(self, alpha, market, model):
        var = self.variance(market, model)
        spot = self.next_mid.spot
        p_down = (spot ** (-2) * (var + spot ** 2) - 1 - (alpha + 1) *
                  (1 / spot * spot - 1)) / ((1 - alpha) * (alpha ** (-2) - 1))
        p_up = (spot ** (-1) * spot - 1 - (alpha ** (-1) - 1) * p_down) / (alpha - 1)
        p_mid = 1 - (p_down + p_up)
        self.p_down = p_down
        self.p_up = p_up
        self.p_mid = p_mid

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

    def has_node_up(self):
        return self.node_up is not None

    def has_node_down(self):
        return self.node_down is not None


def is_close(node, fwd_price):  # Modifier les fonctions pour les mettre dans NODE ?
    up_price = node.spot * ((1 + tree.alpha) / 2)
    down_price = node.spot * ((1 + 1 / tree.alpha) / 2)

    if up_price > fwd_price > down_price:
        return 1
    elif fwd_price > up_price:
        return 2
    else:
        return 0


def create_first_nodes(root_node, market, model, tree_alpha, step):
    # Calculer le prix forward pour le noeud actuel.
    fwd_price = root_node.forward(market, model, step)

    # Créer les trois noeuds suivants pour up, mid, et down.
    root_node.next_up = Node(fwd_price * tree_alpha)
    root_node.next_mid = Node(fwd_price)
    root_node.next_down = Node(fwd_price / tree_alpha)

    # Lier les noeuds up et down des noeuds crées
    link_up_down(root_node)
    Node.calculate_proba(root_node, tree_alpha, market, model)


def link_up_down(node):
    # Relier les noeuds up et down au noeud central.
    node.next_up.node_down = node.next_mid
    node.next_down.node_up = node.next_mid
    # Relier le up et down du noeud mid
    node.next_mid.node_up = node.next_up
    node.next_mid.node_down = node.next_down


def associate_up_down(up_node, down_node):
    up_node.node_down = down_node
    down_node.node_up = up_node


def date_to_step(dividend_date, reference_date, steps_number):
    delta_time = dividend_date - reference_date
    total_days = (option.maturity - reference_date).days
    step_length_in_days = total_days / steps_number
    return delta_time.days / step_length_in_days


def convert_dates_to_steps(dividend_dict, reference_date, steps_number):
    return {date_to_step(date, reference_date, steps_number): amount for date, amount in dividend_dict.items()}


def create_nodes(node, market, model, tree_alpha, step, direction='up'):
    next_direction = "next_" + direction
    node_direction = "node_" + direction

    # Boucle pour parcourir tous les noeuds au dessus/dessous par rapport au noeud entré (noeud root)
    while getattr(node, node_direction) is not None:
        current_node = getattr(node, node_direction)
        fwd_price = current_node.forward(market, model, step)
        check_node = getattr(node, next_direction)
        check = 0
        while check == 0:
            check = is_close(check_node, fwd_price)
            match check:
                case 1:  # Le noeud est close
                    current_node.next_mid = check_node  # association du noeud checké comme next_mid du noeud

                    # Check du noeud up
                    if check_node.has_node_up():  # Le noeud close a un up, on l'associe
                        current_node.next_up = check_node.node_up
                    else:  # Le noeud close n'a pas de up, on le crée
                        new_node = Node(check_node.spot * tree_alpha)  # Création d'un nouveau noeud
                        current_node.next_up = new_node  # Associer le next_up au nouveau noeud
                        associate_up_down(new_node, check_node)  # Associer les up/down des noeuds

                    # Check du noeud down
                    if check_node.has_node_down():  # Le noeud close a un down, on l'associe
                        current_node.next_down = check_node.node_down
                    else:  # Le noeud close n'a pas de down, on le crée
                        new_node = Node(check_node.spot / tree_alpha)  # Création d'un nouveau noeud
                        current_node.next_down = new_node  # Associer le next_down au nouveau noeud
                        associate_up_down(check_node, new_node)

                case 2:  # Le Fwd calculé est plus haut que la borne haute du noeud le plus haut
                    # Association du noeud du checké comme next_down
                    current_node.next_down = check_node
                    # On crée un nouveau mid
                    new_mid_node = Node(check_node.spot * tree_alpha)
                    current_node.next_mid = new_mid_node
                    associate_up_down(new_mid_node, check_node)
                    # On crée un up au nouveau mid
                    new_up_node = Node(new_mid_node.spot * tree_alpha)
                    current_node.next_up = new_up_node  # Associer le next_up au nouveau noeud
                    associate_up_down(new_up_node, new_mid_node)

                case 0:
                    if check_node.has_node_down():  # On regarde si l'on peut encore descendre, si oui on descend
                        check_node = check_node.node_down  # on va vers le noeud du bas
                    else:  # S'il n'y a plus de noeud down, on en créer un qui sera le mid
                        # Association du noeud du checké comme next_down
                        current_node.next_up = check_node
                        # Création d'un nouveau noeud mid
                        new_mid_node = Node(check_node.spot / tree_alpha)
                        current_node.next_mid = new_mid_node
                        associate_up_down(check_node, new_mid_node)
                        # Création du noeud down du nouveau mid
                        new_down_node = Node(new_mid_node.spot / tree_alpha)  # Création du noeud du dessous
                        current_node.next_down = new_down_node  # Associer le next_up au nouveau noeud
                        associate_up_down(new_mid_node, new_down_node)
                        check = 3  # modifier, pas correct
        current_node.calculate_proba(tree_alpha, market, model)  # Calculer les probas du noeud sur lequel on travaille
        node = current_node


def create_next_nodes(root_node, market, model, tree_alpha, step):
    create_first_nodes(root_node, market, model, tree_alpha, step)  # création des 3 premiers noeuds
    create_nodes(root_node, market, model, tree_alpha, step, direction='up')  # création des noeuds du dessus
    create_nodes(root_node, market, model, tree_alpha, step, direction='down')  # création des noeuds du dessous


class Tree:
    def __init__(self, model, market, option):
        self.model = model
        self.market = market
        self.option = option
        self.alpha = self.calculate_alpha()

    def calculate_alpha(self):
        alpha = exp(market.vol * sqrt(3 * model.t_step))
        return alpha

    def create_tree(self, root):
        for i in range(model.steps_nb):
            # Creation des noeuds suivants
            create_next_nodes(root, market, model, tree.alpha, i)
            root = root.next_mid

    def discount_factor(self):
        return exp(-self.market.rate * self.model.t_step)


# main
if __name__ == '__main__':
    # Ajout des paramètres
    option = Option(strike=102, maturity_date="20/03/2024", option_type="Call", option_style="EU")
    model = Model(option, pricing_date="20/09/2023", steps_number=300)
    div = {date(2023, 12, 22): 2, date(2024, 1, 19): 3}
    div_steps = convert_dates_to_steps(div, model.pr_date, model.steps_nb)
    market = Market(volatility=0.25, risk_free_rate=0.02, spot=100, dividends=div_steps)

    print('Market: ' + str(market.parametres()))
    print('Option: ' + str(option.parametres()))
    print('Model: ' + str(model.parametres()))
    print('Dividendes: ' + str(div_steps))
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
