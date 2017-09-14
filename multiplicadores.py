import multiprocessing
import numpy as np
import random

class Multiplicador(multiprocessing.Process):
    def __init__(self,A,B,mutex,sinal,numero,total_threads,contador,Q):
        super(Multiplicador,self).__init__()
        self.A = np.matrix(A)
        self.B = np.matrix(B)
        self.Q = Q
        self.mutex = mutex
        self.tn = numero
        self.p = total_threads
        self.sinal = sinal
        self.contador = contador
        [self.m,self.k] = self.A.shape
        [self.k,self.n] = self.B.shape
        self.C = np.matrix(np.zeros([self.m,self.n]))
        self.inicial = self.tn*int(self.m*self.n/self.p)
        self.final = self.inicial + int(self.m*self.n/self.p)
        if numero == total_threads-1:
            self.final+=int(self.m*self.n%self.p)

    def run(self):
        ele = self.inicial

        #Algoritmo para todos os Elementos Seprados
        while ele<self.final:
            c = 0

            #Calculo de Linha e Coluna do Elemento a Ser calculado
            li = int(ele/self.n) #linha
            cj = ele % self.n #coluna

            #Algoritimo de Multiplicao
            for k in range(0,self.k):
                c += float(self.A[li,k])*float(self.B[k,cj])

            self.C[li,cj] = c

            ele+=1

        #Area Critica
        self.mutex.acquire()
        self.Q.put(self.C)
        self.contador.value+=1

        #Sinaliza Agregador fim do Calculo
        if self.contador.value > self.p -1:
            self.sinal.release()
        self.mutex.release()
        #Fim da Area Critica

class Agregador(multiprocessing.Process):
    def __init__(self,n_threads=4,n_ciclos=100,max_size=1000,min_size=1,quadradas=False):
        super(Agregador,self).__init__()
        self.n_threads=n_threads
        self.n_ciclos=n_ciclos
        self.max_size=max_size
        self.min_size=min_size
        self.quadradas=quadradas #Se a Matrizes serão apenas Quadradas


    def run(self):
        c = 0
        while c<self.n_ciclos:

            #Define se Quadradas
            if self.quadradas:
                m = k = n = random.randrange(self.min_size,self.max_size)
            else:
                m = random.randrange(self.min_size,self.max_size)
                k = random.randrange(self.min_size,self.max_size)
                n = random.randrange(self.min_size,self.max_size)

            #Cria As Matrizes Aleatorias (Float)
            A = np.matrix(np.random.random_sample((m,k)))
            B = np.matrix(np.random.random_sample((k,n)))

            C = np.matrix(np.zeros([m, n]))

            threads = []

            #Inicialização dos Dados Compartilhados
            mutex = multiprocessing.Semaphore(1)
            sinal = multiprocessing.Semaphore(0)
            contador = multiprocessing.Value("i", 0)
            fila = multiprocessing.Queue()

            #Inicia Todas as Threads
            for i in range(0, self.n_threads):
                threads.append(Multiplicador(A, B, mutex, sinal, i, self.n_threads, contador, fila))

            #Roda todas as Threads
            for item in threads:
                item.start()

            #Espera Pelo Sinal
            sinal.acquire()

            mutex.acquire()
            while not fila.empty():
                C += fila.get()
            mutex.release()

            #Escreve A
            arq_name = "A_"+self.name+"_ciclo_"+str(c)+".txt"
            Arq=open(arq_name,"x")
            print_aux(Arq,A)
            Arq.close()

            #Escreve B
            arq_name = "B_" + self.name + "_ciclo_" + str(c) + ".txt"
            Arq = open(arq_name, "x")
            print_aux(Arq,B)
            Arq.close()

            #Escreve C
            arq_name = "C_" + self.name + "_ciclo_" + str(c) + ".txt"
            Arq = open(arq_name, "x")
            print_aux(Arq,C)
            Arq.close()

            #Finaliza Todas as Threads
            for item in threads:
                item.terminate()

            c+=1

def print_aux(file,matrix):
    for row in matrix:
        for item in np.nditer(row):
            file.write(str(item))
            file.write('\t')
        file.write('\n')