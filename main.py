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
import xlwings as xw
import os

# Définir la limite de récursivité et démarrer le timer
sys.setrecursionlimit(100000)

# Récupérer le chemin du répertoire du script actuel et ajouter le nom du fichier Excel
current_directory = os.path.dirname(os.path.abspath(__file__))
excel_file_path = os.path.join(current_directory, 'VBA_Python.xlsm')
wb = xw.Book(excel_file_path)  # L'Excel doit déjà être ouvert
sheet = wb.sheets['Pricer']


def main_function():
    # Récupération des paramètres depuis Excel
    param_list = ['vol', 'rate', 'spot', 'div', 'div_date', 'strike', 'maturity', 'type',
                  'style', 'pr_date', 'steps_nb', 'pruning', 'print_tree', 'print_k', 'print_step']
    params = {}
    for prm in param_list:
        params[prm] = sheet.range(prm).value
    # Création du dictionnaire des div avec conversion des datetime en date
    params['div_date'] = params['div_date'].date()
    div_dict = {params['div_date']: params['div']}

    # Paramètres
    option = Option(strike=params['strike'],
                    maturity_date=params['maturity'],
                    option_type=params['type'],
                    option_style=params['style'])

    model = Model(option.maturity,
                  pricing_date=params['pr_date'],
                  steps_number=int(params['steps_nb']))

    market = Market(volatility=params['vol'],
                    risk_free_rate=params['rate'],
                    spot=params['spot'],
                    dividends=div_dict)

    pruning = params['pruning']
    print_tree = params['print_tree']
    print_fct_k = params['print_k']
    print_fct_step = params['print_step']

    # Affichage des paramètres entrés
    market.param()
    option.param()
    model.param()

    # Start du timer
    start_time = time.time()

    # Initialisation de l'arbre et du premier nœud
    tree = Tree(model, market, option, pruning)
    root = Node(market.spot, 1)
    # Construction de l'arbre
    tree.create_tree(root)

    pr_tree = root.price(option, tree)
    pr_bs = black_scholes(root.spot, option.K, model.t_step * model.steps_nb, market.rate, market.vol, option.call_put)
    # print("\nLe prix de l'option est: " + str(pr_tree))
    sheet.range("py_price").value = str(pr_tree)
    # print("Le prix de l'option avec BS est: " + str(pr_bs))
    sheet.range("bs_price").value = str(pr_bs)
    # print("\nDifférence de prix: " + str(pr_bs - pr_tree))

    #  Affichage du temps d'exécution
    end_time = time.time()
    elapsed_time = end_time - start_time

    # print(f"\nTemps écoulé pour la création de l'arbre et le calcul du prix: {elapsed_time:.5f} secondes")
    sheet.range("py_timer").value = str(f"{elapsed_time:.5f}")

    # Conversion de l'arbre en matrice et écriture de cette matrice dans Excel
    write_to_excel(print_tree, root, model.steps_nb, wb)

    function_of_k(print_fct_k, option, tree, model, market)
    function_of_step(print_fct_step, option, pruning, model, market)


if __name__ == '__main__':
    main_function()
