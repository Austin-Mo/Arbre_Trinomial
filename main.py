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


def get_data():
    # Récupération des paramètres depuis Excel
    param_list = ['vol', 'rate', 'spot', 'div', 'div_date', 'strike', 'maturity', 'type',
                  'style', 'pr_date', 'steps_nb', 'pruning', 'print_tree', 'print_k', 'print_step', 'threshold']
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

    tree = Tree(model=model,
                market=market,
                option=option,
                pruning=params['pruning'],
                threshold=params['threshold'])

    # Création du dictionnaire de données
    data = {
        "option": option,
        "model": model,
        "market": market,
        "tree": tree,
        "pruning": params['pruning'],
        "threshold": params['threshold'],
        "print_tree": params['print_tree'],
        "print_fct_k": params['print_k'],
        "print_fct_step": params['print_step']
    }

    return data


@xw.sub
def main_function():
    # Récupération des datas
    data = get_data()
    option = data['option']
    model = data['model']
    market = data['market']
    tree = data['tree']
    print_tree = data['print_tree']

    # Affichage des paramètres entrés
    market.param()
    option.param()
    model.param()

    # Start du timer
    start_time = time.time()

    # Initialisation du premier nœud et construction de l'arbre
    root = Node(market.spot, 1)
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


@xw.sub
def graphs():
    data = get_data()
    market = data['market']
    option = data['option']
    model = data['model']
    pruning = data['pruning']
    threshold = data['threshold']
    print_fct_k = data['print_fct_k']
    print_fct_step = data['print_fct_step']

    # Graphiques
    function_of_k(print_fct_k, option, pruning, threshold, model, market)
    function_of_step(print_fct_step, option, pruning, threshold, model, market)


if __name__ == '__main__':
    main_function()
    graphs()
