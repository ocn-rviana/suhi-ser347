
# Bibliotecas necessárias
from typing import List

import numpy as np
from numpy.core.multiarray import ndarray


def count_days(bin_array):
    shp_array = bin_array.shape
    row = shp_array[0]
    col = shp_array[1]

    int_array = np.zeros((row,col))

    for r in range(row):
        for c in range(col):
            clear_days = bin(bin_array[r,c])
            days = clear_days[2:].count('1')
            int_array[r,c] = days

    return int_array

def nrs_scale(original_lst, k):
    # Constroi o denominador
    square = original_lst ** 2
    sum_square = np.nansum(square)
    new_lst = original_lst / (sum_square ** 0.5)

    if k == 0:
        N = 25300
    else:
        N = 24100

    output_lst = N * new_lst

    return output_lst

def suhi_index(lst_array, lc_array):
    index_urban = lc_array == 13
    mean_lst_urban = np.nanmean(lst_array[index_urban])

    lc_types = [x for x in range(1,18)]
    lc_types.remove(13)

    shui_value= []

    for lc in lc_types:
        index_urban = lc_array == lc
        mean_lst_lc = np.nanmean(lst_array[index_urban])
        shui = mean_lst_urban - mean_lst_lc
        shui_value.append(shui)

    return shui_value
