import numpy as np
import multiplicadores_reworked as mc
import multiprocessing as mp


A = mc.Agregador(max_size=10,min_size=4,n_ciclos=10,n_threads=4)

A.start()

A.join()