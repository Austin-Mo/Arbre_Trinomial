import numpy as np
from node import Node


# Compter les nœuds d'une colonne à partir d'un nœud du tronc
def count_node(root_node: Node, direction: str) -> int:
    count = 0
    attr_name = "node_" + direction
    while getattr(root_node, attr_name) is not None:
        count += 1
        root_node = getattr(root_node, attr_name)
    return count


# Remplir la matrice avec les noeuds du haut/bas
def fill_up_down(matrix: np.ndarray, root_node, mid_row: int, col: int, direction: str) -> np.ndarray:
    attr_name = "node_" + direction
    if direction == "up":
        move = -1
    else:
        move = 1
    row = mid_row
    while getattr(root_node, attr_name) is not None:
        row += move
        root_node = getattr(root_node, attr_name)
        matrix[row][col] = root_node.spot
    return matrix


# Lecture de l'arbre et conversion de celui_ci en matrice
def tree_to_matrix(root: Node, steps_nb: int) -> np.ndarray:
    center_node = root
    while center_node.next_mid is not None:
        center_node = center_node.next_mid  # Récupérer le dernier nœud du tronc
    count_up = count_node(center_node, direction="up")
    count_down = count_node(center_node, direction="down")

    # Initialiser la matrice
    matrix = np.empty((count_up + count_down + 1, steps_nb + 1))
    matrix.fill(None)

    # Placer le premier nœud dans la première colonne
    mid_row = count_up
    col = 0

    # Lecture de l'arbre et conversion de l'arbre en matrice
    while root is not None:
        matrix[mid_row][col] = root.spot
        matrix = fill_up_down(matrix, root, mid_row, col, direction="up")
        matrix = fill_up_down(matrix, root, mid_row, col, direction="down")
        col += 1
        root = root.next_mid

    return matrix


# Ecriture de l'arbre sur la feuille Python_Tree
def write_to_excel(print_tree: bool, root: Node, stp_nb: int, workbook: 'workbook') -> None:
    if print_tree:
        ws = workbook.sheets["Python_Tree"]
        # Nettoyer la feuille
        ws.clear_contents()
        # Convertir l'arbre en matrice et écrire cette matrice dans Excel
        ws.range('tree').value = tree_to_matrix(root, stp_nb)
