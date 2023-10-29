from scipy.stats import norm
import matplotlib.pyplot as plt
from market import Market
from model import Model
from tqdm import tqdm
from option import Option
from tree import Tree
from printTree import *


def black_scholes(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """
    S: Current stock price
    X: Option strike price
    T: Time to maturity (in years)
    r: Risk-free rate (annual rate)
    sigma: Volatility of the stock (annualized)
    option_type: Either "call" for call option or "put" for put option
    """

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "Call":
        option_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    elif option_type == "Put":
        option_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    else:
        raise ValueError("Invalid option type. Use either 'call' or 'put'.")

    return option_price


def calculate_prices(K: float, model: Model, market: Market, option: Option, pruning: bool,
                     threshold: float) -> (float,float):
    tree = Tree(model, market, option, pruning, threshold)
    root = Node(market.spot, 1)
    tree.create_tree(root)
    tree_price = root.price(option, tree)
    bs_price = black_scholes(root.spot, K, model.t_step * model.steps_nb, market.rate, market.vol, option.call_put)
    return tree_price, bs_price


def function_of_k(print_fct_k: bool, option: Option, pruning: bool, threshold: float,
                  model: Model, market: Market) -> None:
    if print_fct_k:
        entered_k = option.K
        market.div = {}
        # Création de listes pour stocker les valeurs
        k_values, bs_prices, tree_prices, diffs = [], [], [], []

        for K in tqdm(range(round(market.spot/2), round(market.spot*1.8))):
            option.K = K
            # Calcul des prix avec l'arbre et BS
            tree_price, bs_price = calculate_prices(K, model, market, option, pruning, threshold)

            # Ajouter les valeurs aux listes
            k_values.append(K)
            bs_prices.append(bs_price)
            tree_prices.append(tree_price)
            diffs.append(tree_price - bs_price)

        # Affichage du graphique
        plt.figure(num=1, figsize=(10, 5))

        ax1 = plt.gca()  # Récupération de l'axe actuel
        ax2 = ax1.twinx()  # Création d'un deuxième axe Y

        # Black-Scholes Price vs K
        ax1.plot(k_values, bs_prices, color='blue', label='BS Price', linestyle='-')
        # Tree Price vs K
        ax1.plot(k_values, tree_prices, color='green', label='Tree Price', linestyle='-')

        # Difference vs K (sur le deuxième axe Y)
        ax2.plot(k_values, diffs, color='red', label='Tree - BS Price', linestyle='-', alpha=0.7)

        ax1.set_xlabel('K')
        ax1.set_ylabel('Option Price', color='blue')
        ax2.set_ylabel('Difference', color='red')
        ax1.set_title('Tree vs. Black-Scholes Price function of K')

        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')

        ax1.grid(True)
        plt.tight_layout()
        plt.show()

        option.K = entered_k  # remettre le k de base


def function_of_step(print_fct_step: bool, option: Option, pruning: bool, threshold: float, model: Model,
                     market: Market) -> None:
    if print_fct_step:
        entered_step = model.steps_nb
        market.div = {}
        # Création de listes pour stocker les valeurs
        step_values, bs_prices, tree_prices, diffs = [], [], [], []

        for steps_nb in tqdm(range(1, 500)):
            model.steps_nb = steps_nb
            model.t_step = model.calculate_t_step()
            # Calcul des prix avec l'arbre et BS
            tree_price, bs_price = calculate_prices(option.K, model, market, option, pruning, threshold)

            # Ajouter les valeurs aux listes
            step_values.append(steps_nb)
            bs_prices.append(bs_price)
            tree_prices.append(tree_price)
            diffs.append((tree_price - bs_price) * steps_nb)

        # Affichage du graphique
        plt.figure(num=2, figsize=(10, 5))
        plt.plot(step_values, diffs, color='red', linestyle='-')
        plt.xlabel('Steps')
        plt.title('(Tree - Black-Scholes) * NbSteps')
        plt.legend()
        plt.grid(True)

        plt.tight_layout()
        plt.show()

        model.steps_nb = entered_step
