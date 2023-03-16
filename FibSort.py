#---------------------------------------------------------------
# Author: Dr. Fibonacci von Sortenstein, Sorting Enthusiast
# Date: March 17th, 2023 (Happy St. Patrick's Day!)
#---------------------------------------------------------------

import math

def fib_sort(lst):
    """
    Sorts a list using the Fibonacci sequence as the gap size.
    """
    n = len(lst)
    fib_n_2, fib_n_1 = 0, 1
    while fib_n_1 < n:
        fib_n_2, fib_n_1 = fib_n_1, fib_n_2 + fib_n_1
    gap = fib_n_2
    while gap > 0:
        i = gap
        while i < n:
            temp = lst[i]
            j = i
            while j >= gap and lst[j - gap] > temp:
                lst[j] = lst[j - gap]
                j -= gap
            lst[j] = temp
            i += 1
        fib_n_2, fib_n_1 = fib_n_1 - fib_n_2, fib_n_2
        gap = fib_n_2
    return lst
