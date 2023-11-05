from math import exp
from market import Market
from model import Model
from node import Node
from nodeCreation import NodeCreation
from option import Option


class Tree:
    def __init__(self, model: Model, market: Market, option: Option, pruning: float, threshold: float) -> None:
        self.model = model
        self.market = market
        self.option = option
        self.pruning = pruning
        self.threshold = threshold
        self.NodeCreation = NodeCreation(self.market, self.model, self.pruning, self.threshold)

    def create_tree(self, root: Node) -> None:
        for i in range(self.model.steps_nb):
            # Creation des noeuds suivants
            self.NodeCreation.create_next_nodes(root, i)
            root = root.next_mid

    def discount_factor(self) -> float:
        return exp(-self.market.rate * self.model.t_step)
