# Importation des modules
from node import Node
from model import Model
from option import Option
from market import Market
from tree import Tree
from testing import *
from printTree import *
from datetime import date
import time
import sys

# Définir la limite de récursivité et démarrer le timer
sys.setrecursionlimit(100000)
start_time = time.time()


if __name__ == '__main__':
    # Paramètres
    option = Option(strike=108.88, maturity_date="07/12/2022", option_type="Call", option_style="EU")
    model = Model(option.maturity, pricing_date="18/02/2022", steps_number=1000)
    div = {date(2022, 4, 2): 1.66}
    market = Market(volatility=0.1077, risk_free_rate=0.0971, spot=163.73, dividends=div)
    pruning = True
    print_tree = False
    print_fct_k = False
    print_fct_step = False

    # Affichage des paramètres entrés
    market.param()
    option.param()
    model.param()

    # Initialisation de l'arbre et du premier nœud
    tree = Tree(model, market, option, pruning)
    root = Node(market.spot, 1)
    # Construction de l'arbre
    tree.create_tree(root)

    pr_tree = root.price(option, tree)
    pr_bs = black_scholes(root.spot, option.K, model.t_step*model.steps_nb, market.rate, market.vol, option.call_put)
    print("\nLe prix de l'option est: " + str(pr_tree))
    print("Le prix de l'option avec BS est: " + str(pr_bs))
    print("\nDifférence de prix: " + str(pr_bs - pr_tree))

    #  Affichage du temps d'exécution
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"\nTemps écoulé calcul du prix: {elapsed_time:.5f} secondes")

    # Conversion de l'arbre en matrice et écriture de cette matrice dans Excel
    write_to_excel(print_tree, root, model.steps_nb)

    function_of_k(print_fct_k, option, tree, model, market)
    function_of_step(print_fct_step, option, pruning, model, market)
