import numpy as np
import xlwings as xw


def count_node(root_node, direction):
    count = 0
    attr_name = "node_" + direction
    while getattr(root_node, attr_name) is not None:
        count += 1
        root_node = getattr(root_node, attr_name)
    return count


def fill_up_down(matrix, root_node, mid_row, col, direction):
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


def tree_to_matrix(root, steps_nb):
    center_node = root
    while center_node.next_mid is not None:
        center_node = center_node.next_mid  # Récupérer le dernier noeud du centre
    count_up = count_node(center_node, direction="up")
    count_down = count_node(center_node, direction="down")

    # Initialiser la matrice
    matrix = np.empty((count_up + count_down + 1, steps_nb + 1))
    matrix.fill(None)

    # Placer le premier noeud dans la première colonne
    mid_row = count_up
    col = 0

    while root is not None:
        matrix[mid_row][col] = root.spot
        matrix = fill_up_down(matrix, root, mid_row, col, direction="up")
        matrix = fill_up_down(matrix, root, mid_row, col, direction="down")
        col += 1
        root = root.next_mid

    return matrix


def write_to_excel(print_tree, root, stp_nb, workbook):
    if print_tree:
        ws = workbook.sheets["Python_Tree"]
        # Nettoyer la feuille
        ws.clear_contents()
        # Convertir l'arbre en matrice et écrire cette matrice dans Excel
        ws.range('A1').value = tree_to_matrix(root, stp_nb)
