import multiprocessing
import numpy as np
import random
import ctypes

class Multiplicador(multiprocessing.Process):
    def __init__(self,man,mutex,sinal,numero,total_threads,contador,Q,barreira_entrada,barreira_saida):
        super(Multiplicador,self).__init__()
        self.man = man
        self.Q = Q
        self.mutex = mutex
        self.tn = numero
        self.p = total_threads
        self.sinal = sinal
        self.contador = contador
        self.barreira_entrada = barreira_entrada
        self.barreira_saida = barreira_saida


    def run(self):
        ci = 0
        while True:
            self.barreira_entrada.acquire()
            self.barreira_entrada.release()

            self.mutex.acquire()
            A = self.man.A.copy()
            B = self.man.B.copy()
            self.mutex.release()

            [self.m, self.k] = A.shape
            [self.k, self.n] = B.shape
            self.C = np.matrix(np.zeros([self.m, self.n]))

            inicial = self.tn * int(self.m * self.n / self.p)
            self.final = inicial + int(self.m * self.n / self.p)
            if self.tn == self.p - 1:
                self.final += int(self.m * self.n % self.p)

            ele = inicial

            #Algoritmo para todos os Elementos Seprados
            while ele<self.final:


                c = 0

                #Calculo de Linha e Coluna do Elemento a Ser calculado
                li = int(ele/self.n) #linha
                cj = ele % self.n #coluna

                #Algoritimo de Multiplicao
                for k in range(0,self.k):
                    c += float(A[li,k])*float(B[k,cj])

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

            #Fim da Area Critica, inicio barreira de Saida
            self.barreira_saida.acquire()
            self.barreira_saida.release()
            ci+=1

class Agregador(multiprocessing.Process):
    def __init__(self,n_threads=4,n_ciclos=100,max_size=10000,min_size=1,quadradas=False):
        super(Agregador,self).__init__()
        if n_threads<1:
            self.n_threads = int(multiprocessing.cpu_count())
        else:
            self.n_threads=n_threads
        print("Processo de Multiplicação com "+str(self.n_threads)+" cores")
        self.n_ciclos=n_ciclos
        self.max_size=max_size
        self.min_size=min_size
        self.quadradas=quadradas #Se a Matrizes serão apenas Quadradas


    def run(self):
        c = 0

        manager = multiprocessing.Manager()
        name_space = manager.Namespace()

        threads = []

        # Inicialização dos Dados Compartilhados
        mutex = multiprocessing.Semaphore(1)
        sinal = multiprocessing.Semaphore(0)
        contador = multiprocessing.Value("i", 0)
        barreira_entrada = multiprocessing.Semaphore(0)
        barreira_saida = multiprocessing.Semaphore(1)
        fila = multiprocessing.Queue()

        # Inicia Todas as Threads
        for i in range(0, self.n_threads):
            threads.append(Multiplicador(name_space, mutex, sinal, i, self.n_threads, contador, fila, barreira_entrada, barreira_saida))

        # Roda todas as Threads
        for item in threads:
            item.start()

        while c<self.n_ciclos:

            #Define se Quadradas
            if self.quadradas:
                m = k = n = random.randrange(self.min_size,self.max_size)
            else:
                m = random.randrange(self.min_size,self.max_size)
                k = random.randrange(self.min_size,self.max_size)
                n = random.randrange(self.min_size,self.max_size)

            #Cria As Matrizes Aleatorias (Float)
            Ar = np.matrix(np.random.random_sample((m,k)))
            Br = np.matrix(np.random.random_sample((k,n)))

            C = np.matrix(np.zeros([m, n]))

            mutex.acquire()
            name_space.A = Ar
            name_space.B = Br
            mutex.release()

            #Sinaliza Barreira de Entradas Que Pode iniciar trabalhos
            barreira_saida.acquire()
            barreira_entrada.release()

            #Espera Pelo Sinal
            sinal.acquire()
            barreira_entrada.acquire()

            mutex.acquire()
            contador.value = 0
            while not fila.empty():
                C += fila.get()
            mutex.release()

            #Escreve A
            arq_name = "A_"+self.name+"_ciclo_"+str(c)+".txt"
            Arq=open(arq_name,"w")
            print_aux(Arq,Ar)
            Arq.close()

            #Escreve B
            arq_name = "B_" + self.name + "_ciclo_" + str(c) + ".txt"
            Arq = open(arq_name, "w")
            print_aux(Arq,Br)
            Arq.close()

            #Escreve C
            arq_name = "C_" + self.name + "_ciclo_" + str(c) + ".txt"
            Arq = open(arq_name, "w")
            print_aux(Arq,C)
            Arq.close()

            print("Ciclo de Calculo "+str(c)+" completo")

            barreira_saida.release()

            c+=1

        # Finaliza Todas as Threads
        for item in threads:
            item.terminate()


def print_aux(file,matrix):
    for row in matrix:
        for item in np.nditer(row):
            file.write(str(item))
            file.write('\t')
        file.write('\n')