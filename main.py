import numpy as np
import multiplicadores_reworked as mc
import multiprocessing as mp


A = mc.Agregador(max_size=1000,min_size=2,n_ciclos=3,n_threads=0)

A.start()

A.join()