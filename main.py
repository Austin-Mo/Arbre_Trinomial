# Creation Arbre

from math import *
from datetime import datetime, date, timedelta


class Market:
    def __init__(self, volatility, risk_free_rate, spot, dividends):
        self.vol = volatility
        self.rate = risk_free_rate
        self.spot = spot
        self.div = dividends

    def parametres(self):
        return self.vol, self.rate, self.spot, self.spot, self.div


class Option:
    def __init__(self, strike, maturity_date, option_type):
        self.K = strike
        self.maturity = datetime.strptime(maturity_date, "%d/%m/%Y").date()
        self.type = option_type

    def parametres(self):
        return self.K, self.maturity, self.type


class Model:
    def __init__(self, option, pricing_date, steps_number):
        self.option = option
        self.pr_date = datetime.strptime(pricing_date, "%d/%m/%Y").date()
        self.steps_nb = steps_number
        self.t_step = ((option.maturity - self.pr_date) / self.steps_nb).total_seconds() / 86400 / 365  # En année

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

        Node.all_nodes.append(self)

    @classmethod
    def display_all_nodes(cls):
        for node in cls.all_nodes:
            print(node)

    def __repr__(self):
        return str(self.spot)

    def forward(self, market, model, date):
        if date in market.div:
            dividend = market.div[date]
            fwd_price = (self.spot - dividend) * exp(market.rate * model.t_step)
        else:
            fwd_price = self.spot * exp(market.rate * model.t_step)
        return fwd_price

    def variance(self, market, model):
        var = self.spot**2*exp(2*market.rate*model.t_step)*(exp(market.vol**2*model.t_step)-1)
        return var


def is_close(node, fwd_price):
    up_price = node.spot*((1+tree.alpha)/2)
    down_price = node.spot*((1+1/tree.alpha)/2)

    if up_price > fwd_price > down_price:
        return 1
    else:
        return 0


def create_first_nodes(root_node, market, model, tree_alpha, date):
    # Calculer le prix forward pour le noeud actuel.
    fwd_price = root_node.forward(market, model, date)

    # Créer les trois noeuds suivants pour up, mid, et down.
    root_node.next_up = Node(fwd_price * tree_alpha)
    root_node.next_mid = Node(fwd_price)
    root_node.next_down = Node(fwd_price / tree_alpha)

    # Lier les noeuds up et down des noeuds crées
    link_up_down(root_node)


def link_up_down(node):
    # Relier les noeuds up et down au noeud central.
    node.next_up.node_down = node.next_mid
    node.next_down.node_up = node.next_mid
    # Relier le up et down du noeud mid
    node.next_mid.node_up = node.next_up
    node.next_mid.node_down = node.next_down


def create_nodes(node, market, model, tree_alpha, date, direction='up'):
    next_direction = "next_" + direction
    node_direction = "node_" + direction
    opposite_direction = "down" if direction == "up" else "up"

    # Boucle pour parcourir tous les noeuds au dessus/dessous du noeud central
    while getattr(node, node_direction) is not None:
        current_node = getattr(node, node_direction)
        fwd_price = current_node.forward(market, model, date)

        check_node = getattr(node, next_direction)
        check = 0
        while check == 0:
            check = is_close(check_node, fwd_price)
            if check == 1:
                setattr(current_node, "next_mid", check_node)
                setattr(current_node, next_direction, getattr(check_node, node_direction))

                if getattr(check_node, node_direction) is None:
                    if direction == "up":
                        new_node = Node(check_node.spot * tree_alpha)
                    else:
                        new_node = Node(check_node.spot / tree_alpha)
                    setattr(current_node, next_direction, new_node)
                    setattr(new_node, "node_" + opposite_direction, check_node)
                    setattr(check_node, "node_" + direction, new_node)
                else:
                    setattr(current_node, next_direction, getattr(check_node, next_direction))
            else:
                check_node = getattr(check_node, "node_" + direction)
                check = 1
        node = current_node


def create_next_nodes(root_node, market, model, tree_alpha, date):

    create_first_nodes(root_node, market, model, tree_alpha, date)  # création des 3 premiers noeuds
    create_nodes(root_node, market, model, tree_alpha, date, direction='up')  # création des noeuds du dessus
    create_nodes(root_node, market, model, tree_alpha, date, direction='down')  # création des noeuds du dessous


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
        # Boucle pour créer l'arbre en entier
        i = 0
        date = model.pr_date + timedelta(days=1)
        while i < model.steps_nb:
            # Creation des noeuds suivants
            create_next_nodes(root, market, model, tree.alpha, date)
            root = root.next_mid
            i += 1
            date = date + timedelta(days=1)


# main
if __name__ == '__main__':
    # Ajout des paramètres
    dividends = {date(2023, 9, 23): 2, date(2023, 9, 25): 3}

    market = Market(0.25, 0.04, 100, dividends)
    option = Option(102, "19/09/2024", "Call")
    model = Model(option, "20/09/2023", 3)
    print('Market: ' + str(market.parametres()))
    print('Option: ' + str(option.parametres()))
    print('Model: ' + str(model.parametres()))

    # Creation de l'arbre
    tree = Tree(model, market, option)
    print(f"Alpha: {tree.alpha} Times step: {tree.model.t_step}")

    print("\n")

    # Création du noeud initial
    root = Node(market.spot)

    # Appel de la fonction créer arbre
    tree.create_tree(root)

    Node.display_all_nodes()  # test


