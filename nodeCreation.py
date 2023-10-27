from node import Node
from math import *


class NodeCreation:
    def __init__(self, market, model, pruning, threshold):
        self.market = market
        self.model = model
        self.check_node = None
        self.current_node = None
        self.fwd_price = None
        self.div_steps = self.convert_dates_to_steps(market.div, model.pr_date)
        self.alpha = self.calculate_alpha()
        self.steps_over_nodes = False
        self.node_direction = None
        self.next_direction = None
        self.node_opposite_direction = None
        self.next_opposite_direction = None
        self.transition_node = None
        self.p_transition = 0 if pruning else 1
        self.threshold = threshold

    def convert_dates_to_steps(self, dividend_dict, reference_date):
        return {self.date_to_annual_time_measure(date, reference_date): amount for date, amount in
                dividend_dict.items()}

    @staticmethod
    def date_to_annual_time_measure(dividend_date, reference_date):
        return (dividend_date - reference_date).days / 365

    def calculate_alpha(self):
        alpha = exp(self.market.vol * sqrt(3 * self.model.t_step))
        return alpha

    def compute_div(self, step):
        dividend = 0
        for key_step in self.div_steps.keys():
            if (step + 1) * self.model.t_step >= key_step > step * self.model.t_step:
                dividend += self.div_steps[key_step]  # créer un dictionnaire avec des dates correspondant à une étape
        return dividend

    def create_next_nodes(self, root_node, step):
        dividend = self.compute_div(step)
        div_bool = True if dividend == 0 else False
        self.create_first_nodes(root_node, dividend)  # création des 3 premiers nœuds
        if div_bool is True and self.steps_over_nodes is False:
            self.create_nodes(root_node, 1)  # création des nœuds du dessus
            self.create_nodes(root_node, -1)  # création des nœuds du dessous
        else:
            # si on a "sauté" des nœuds au tour précédent (dans up_and_above ou down_and_bellow)
            # ou si on a des dividendes
            # alors il faut checker is_close
            # on remet self.step_over_nodes à sa valeur par défaut
            self.steps_over_nodes = False
            self.create_nodes_and_check_is_close(root_node, dividend, 1)  # création des noeuds du dessus
            self.create_nodes_and_check_is_close(root_node, dividend, -1)  # création des noeuds du dessous

    def create_first_nodes(self, root_node, dividend):
        # Calculer le prix forward pour le noeud actuel.
        self.fwd_price = root_node.forward(self.market, self.model) - dividend

        # Créer les trois noeuds suivants pour up, mid, et down.
        root_node.next_up = Node(self.fwd_price * self.alpha, self.p_transition)
        root_node.next_mid = Node(self.fwd_price, self.p_transition)
        root_node.next_down = Node(self.fwd_price / self.alpha, self.p_transition)

        # Lier les noeuds up et down des noeuds crées
        Node.associate_up_down(root_node.next_up, root_node.next_mid)
        Node.associate_up_down(root_node.next_mid, root_node.next_down)
        Node.calculate_proba(root_node, self.alpha, self.market, self.model, dividend)

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
        self.fwd_price = self.current_node.forward(self.market, self.model) - dividend
        if self.fwd_price < 0:
            raise ValueError(f"Error, negative forward {self} !")

    def create_nodes_and_check_is_close(self, node, dividend, direction):
        self.get_direction(node, direction)
        # Boucle pour parcourir tous les nœuds au-dessus/dessous par rapport au nœud entré (nœud root)
        while getattr(self.current_node, self.node_direction) is not None:
            self.get_parameters(self.node_direction, self.next_direction, dividend)
            check = self.is_close(self.check_node, self.fwd_price) * direction - direction

            if getattr(self.current_node, self.node_direction) is None and self.current_node.p_transition < self.threshold:
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
                self.current_node.calculate_proba(self.alpha, self.market, self.model,
                                                  dividend)  # Calculer les probas du nœud sur lequel on travaille

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
            if getattr(self.current_node, self.node_direction) is None and self.current_node.p_transition < self.threshold:
                self.current_node.next_mid = self.check_node

            else:
                self.when_is_close(direction)
                self.current_node.calculate_proba(self.alpha, self.market, self.model, 0)

    def is_close(self, node, fwd_price):
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
        on crée des noeuds vers le haut mais fwd est tjs > check_node
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
