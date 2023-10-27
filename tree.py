from node import *
from nodeCreation import *


class Tree:
    def __init__(self, model, market, option, pruning, threshold):
        self.model = model
        self.market = market
        self.option = option
        self.pruning = pruning
        self.NodeCreation = NodeCreation(self.market, self.model, self.pruning, threshold)

    def create_tree(self, root):
        for i in range(self.model.steps_nb):
            # Creation des noeuds suivants
            self.NodeCreation.create_next_nodes(root, i)
            root = root.next_mid

    def discount_factor(self):
        return exp(-self.market.rate * self.model.t_step)
