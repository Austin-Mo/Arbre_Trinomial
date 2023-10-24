# Importation des modules
from node import Node
from model import Model
from option import Option
from market import Market
from tree import Tree
from printTree import *
from datetime import date
import time
import sys

# Définir la limite de récursivité et démarrer le timer
sys.setrecursionlimit(100000)
start_time = time.time()


def main():
    # Paramètres
    option = Option(strike=108.88, maturity_date="07/12/2022", option_type="Call", option_style="EU")
    model = Model(option, pricing_date="18/02/2022", steps_number=75)
    div = {date(2022, 4, 2): 1.66}
    market = Market(volatility=0.1077, risk_free_rate=0.0971, spot=163.73, dividends=div)
    pruning = True
    print_tree = True

    # Affichage des paramètres entrés
    market.param()
    option.param()
    model.param()

    # Création de l'arbre et du premier noeud
    tree = Tree(model, market, option, pruning)
    root = Node(market.spot, 1)

    # Construction de l'arbre
    tree.create_tree(root)
    print("\nLe prix de l'option est: " + str(root.price(option, tree)))

    # Conversion de l'arbre en matrice et écriture de cette matrice dans Excel
    write_to_excel(print_tree, root, model.steps_nb)

    # Affichage du temps d'exécution
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Temps écoulé: {elapsed_time:.5f} secondes")


if __name__ == '__main__':
    main()
