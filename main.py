# Creation Arbre
from math import *
from datetime import datetime, date
import xlwings as xw

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

    def forward(self, market, model):  # t_step ?
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

    def price(self, option):
        df = tree.discount_factor()
        if self.next_mid is None:
            self.pr_opt = option.payoff(self.spot)
        elif self.pr_opt is None:
            if self.next_up is None:
                self.pr_opt = df * self.next_mid.price(option)
                if option.type == 'US':
                    self.pr_opt = max(self.pr_opt, option.payoff(self.spot))
            else:
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
    def __init__(self, market, model, pruning):
        self.market = market
        self.model = model
        self.check_node = None
        self.current_node = None
        self.fwd_price = None
        self.div_steps = self.convert_dates_to_steps(market.div, model.pr_date, model.steps_nb)
        self.alpha = self.calculate_alpha()
        self.steps_over_nodes = False
        self.node_direction = None
        self.next_direction = None
        self.node_opposite_direction = None
        self.next_opposite_direction = None
        self.transition_node = None
        self.p_transition = 0 if pruning == 'True' else 1

    def convert_dates_to_steps(self, dividend_dict, reference_date, steps_number):
        return {self.date_to_annual_time_measure(date, reference_date, steps_number): amount for date, amount in
                dividend_dict.items()}

    @staticmethod
    def date_to_annual_time_measure(dividend_date, reference_date, steps_number):
        return (dividend_date - reference_date).days / 365

    def calculate_alpha(self):
        alpha = exp(market.vol * sqrt(3 * model.t_step))
        return alpha

    def compute_div(self, step):
        dividend = 0
        for key_step in self.div_steps.keys():
            if (step + 1) * model.t_step >= key_step > step * model.t_step:  # step+1 ?
                dividend += self.div_steps[key_step]  # créer un dictionnaire avec des dates correspondant à une étape
        return dividend

    def create_next_nodes(self, root_node, step):
        dividend = self.compute_div(step)
        div_bool = True if dividend == 0 else False
        self.create_first_nodes(root_node, dividend)  # création des 3 premiers noeuds
        if div_bool is True and self.steps_over_nodes is False:
            self.create_nodes(root_node, 1)  # création des noeuds du dessus
            self.create_nodes(root_node, -1)  # création des noeuds du dessous
        else:
            # si on a "sauté" des neuds au tour précédent (dans up_and_above ou down_and_bellow)
            # ou si on a des dividendes
            # alors il faut checker is_close
            # on remet self.step_over_nodes à sa valeur par défaut
            self.steps_over_nodes = False
            self.create_nodes_and_check_is_close(root_node, dividend, 1)  # création des noeuds du dessus
            self.create_nodes_and_check_is_close(root_node, dividend, -1)  # création des noeuds du dessous

    def create_first_nodes(self, root_node, dividend):
        # Calculer le prix forward pour le noeud actuel.
        self.fwd_price = root_node.forward(market, model) - dividend

        # Créer les trois noeuds suivants pour up, mid, et down.
        root_node.next_up = Node(self.fwd_price * self.alpha, self.p_transition)
        root_node.next_mid = Node(self.fwd_price, self.p_transition)
        root_node.next_down = Node(self.fwd_price / self.alpha, self.p_transition)

        # Lier les noeuds up et down des noeuds crées
        Node.associate_up_down(root_node.next_up, root_node.next_mid)
        Node.associate_up_down(root_node.next_mid, root_node.next_down)
        Node.calculate_proba(root_node, self.alpha, market, model, dividend)

    def get_direction(self, node, direction):
        self.current_node = node
        match direction:
            case 1:
                self.next_direction = "next_up"
                self.node_direction = "node_up"
                self.next_opposite_direction = "next_down"
                self.node_opposite_direction = "node_down"
            case -1:
                self.next_direction = "next_down"
                self.node_direction = "node_down"
                self.next_opposite_direction = "next_up"
                self.node_opposite_direction = "node_up"

    def get_parameters(self, node_direction, next_direction, dividend):
        self.check_node = getattr(self.current_node, next_direction)
        self.current_node = getattr(self.current_node, node_direction)
        self.fwd_price = max(self.current_node.forward(market, model) - dividend, 0.01)

    def create_nodes_and_check_is_close(self, node, dividend, direction):
        self.get_direction(node, direction)
        # Boucle pour parcourir tous les noeuds au dessus/dessous par rapport au noeud entré (noeud root)
        while getattr(self.current_node, self.node_direction) is not None:
            self.get_parameters(self.node_direction, self.next_direction, dividend)
            check = self.is_close(self.check_node, self.fwd_price) * direction - direction

            if getattr(self.current_node, self.node_direction) is None and self.current_node.p_transition < 0.18 ** 400:
                self.all_in_next_mid(check, direction)
            else:
                # check compare le fwd et check_node mais aussi la direction (1, -1) pour qu'on sache dans quel cas on se trouve (cf. when_inside et when_outside)
                match check:
                    case 0:
                        self.when_is_close(direction)
                    case 1:
                        self.when_outside(direction)
                    case -1:
                        self.when_inside(direction)
                self.current_node.calculate_proba(self.alpha, market, model,
                                                  dividend)  # Calculer les probas du noeud sur lequel on travaille

    def all_in_next_mid(self, check, direction):
        match check:
            case 0:
                self.current_node.next_mid = self.check_node
            case 1:
                new_node = Node(self.check_node.spot * self.alpha ** direction, self.p_transition)
                while self.is_close(new_node, self.fwd_price) - direction == 1:
                    new_node = Node(new_node.spot * self.alpha ** direction, self.p_transition)
                self.current_node.next_mid = new_node
                setattr(self.check_node, self.node_direction, new_node)
                setattr(new_node, self.node_opposite_direction, self.check_node)
            case -1:
                self.current_node.next_mid = getattr(self.check_node, self.node_opposite_direction)

    def create_nodes(self, node, direction):
        self.get_direction(node, direction)
        # Boucle pour parcourir tous les noeuds au dessus/dessous par rapport au noeud entré (noeud root)
        while getattr(self.current_node, self.node_direction) is not None:
            self.get_parameters(self.node_direction, self.next_direction, 0)
            # Use the dictionary to execute the appropriate code block
            if getattr(self.current_node, self.node_direction) is None and self.current_node.p_transition < 0.18 ** 400:
                self.current_node.next_mid = self.check_node

            else:
                self.when_is_close(direction)
                self.current_node.calculate_proba(self.alpha, market, model, 0)

    def is_close(self, node, fwd_price):  # Modifier les fonctions pour les mettre dans NODE ?
        up_price = node.spot * ((1 + self.alpha) / 2)
        down_price = node.spot * ((1 + 1 / self.alpha) / 2)
        if fwd_price < down_price:
            return 0
        elif fwd_price > up_price:
            return 2
        else:
            return 1

    def when_is_close(self, direction):
        """
        is_close = True self.check_node est bien le next_mid de self.current_node
        on crée le next_up/next_down de self.current_node
        on relie les next et le new_node avec le self.check_node
        """
        new_node = Node(self.check_node.spot * self.alpha ** direction, self.p_transition)
        setattr(self.current_node, self.next_direction, new_node)
        self.current_node.next_mid = self.check_node
        setattr(self.current_node, self.next_opposite_direction, getattr(self.check_node, self.node_opposite_direction))
        setattr(self.check_node, self.node_direction, new_node)
        setattr(new_node, self.node_opposite_direction, self.check_node)

    def when_outside(self, direction):
        """
        on crée des neuds vers le haut mais fwd est tjs > check_node
        ou bien on crée des neuds vers le bas mais fwd tjs < check_node
        on crée un transition node et on voit si c'est suffisant
        sinon on entre dans still_outside
        """
        self.transition_node = self.check_node
        self.check_node = Node(self.check_node.spot * self.alpha ** direction, self.p_transition)
        if self.is_close(self.check_node, self.fwd_price) - direction == 1:
            self.still_outside(direction)

        setattr(self.check_node, self.node_opposite_direction, self.transition_node)
        setattr(self.transition_node, self.node_direction, self.check_node)
        self.when_is_close(direction)

    def still_outside(self, direction):
        memory_node = self.transition_node
        while self.is_close(self.check_node, self.fwd_price) - direction == 1:
            self.steps_over_nodes = True
            self.transition_node = self.check_node
            self.check_node = Node(self.check_node.spot * self.alpha ** direction, self.p_transition)
        setattr(self.transition_node, self.node_opposite_direction, memory_node)
        setattr(memory_node, self.node_direction, self.transition_node)

    def when_inside(self):
        """
         on crée vers le haut mais fwd < check_node ou vers le bas mais fwd > check_node
         les 3 nexts de current_node sont les mêmes que les trois nexts de current_node.node_down (cas vers le haut) ou current_node.node_up (cas vers le bas)
        """
        current_node_node_opposite_direction = getattr(self.current_node, self.node_opposite_direction)
        self.current_node.next_down = current_node_node_opposite_direction.next_down
        self.current_node.next_mid = current_node_node_opposite_direction.next_mid
        self.current_node.next_up = current_node_node_opposite_direction.next_up


class Tree:
    def __init__(self, model, market, option, pruning):
        self.model = model
        self.market = market
        self.option = option
        self.pruning = pruning
        self.NodeCreation = NodeCreation(self.market, self.model, self.pruning)

    def create_tree(self, root):
        for i in range(model.steps_nb):
            # Creation des noeuds suivants
            self.NodeCreation.create_next_nodes(root, i)
            root = root.next_mid

    def discount_factor(self):
        return exp(-self.market.rate * self.model.t_step)


def tree_to_matrix(root, steps_nb):
    # Initialize the matrix with None
    matrix = [[None for _ in range(steps_nb + 1)] for _ in range(2*steps_nb + 1)]

    # Set the root in the middle of the first column
    mid_row = steps_nb
    col = 0

    while root is not None:
        mid_row = steps_nb
        matrix[mid_row][col] = root.spot
        node = root
        mid_row = steps_nb
        while node.node_up is not None:
            mid_row -= 1
            node = node.node_up
            matrix[mid_row][col] = node.spot
        node = root
        mid_row = steps_nb
        while node.node_down is not None:
            mid_row += 1
            node = node.node_down
            matrix[mid_row][col] = node.spot
        col += 1
        root = root.next_mid

    return matrix


def write_to_excel(matrix):
    wb = xw.Book()
    ws = wb.sheets[0]
    ws.range('A1').value = matrix


# main
if __name__ == '__main__':
    # Ajout des paramètres
    option = Option(strike=108.88, maturity_date="07/12/2022", option_type="Call", option_style="EU")
    model = Model(option, pricing_date="18/02/2022", steps_number=200)
    div = {date(2022, 4, 2): 1.66}
    pruning = "True"
    market = Market(volatility=0.1077, risk_free_rate=0.0971, spot=163.73, dividends=div)

    print('Market: ' + str(market.parametres()))
    print('Option: ' + str(option.parametres()))
    print('Model: ' + str(model.parametres()))
    # Creation de l'arbre
    tree = Tree(model, market, option, pruning)
    #    print(f"Alpha: {tree.alpha} Times step: {tree.model.t_step} \n")

    # Création du noeud initial
    root = Node(market.spot, 1)
    # Appel de la fonction créer arbre
    tree.create_tree(root)

    # Node.display_all_nodes()

    print("\nLe prix de l'option est: " + str(root.price(option)))

    # Convertir l'arbre en matrice et écrire cette matrice dans Excel
    matrix_representation = tree_to_matrix(root, model.steps_nb)
    write_to_excel(matrix_representation)

    # Tester le temps d'exécution
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Temps écoulé: {elapsed_time:.5f} secondes")
