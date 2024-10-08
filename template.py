import numpy as np
import json 
from utils import puntaje_y_no_usados, JUGADA_PLANTARSE, JUGADA_TIRAR, JUGADAS_STR
from collections import defaultdict
from tqdm import tqdm
from jugador import Jugador

class AmbienteDiezMil:
    
    def __init__(self):
        """Definir las variables de instancia de un ambiente.
        ¿Qué es propio de un ambiente de 10.000?
        """
        self.puntaje_total = 0
        self.puntaje_turno = 0
        self.dados = [1, 2, 3, 4, 5, 6]  # se tiran los 6 dados cuando aranca el juego
        self.termino = False  # flag para indicar si el turno termino
        self.turnos = 1 

    def reset(self):
        """Reinicia el ambiente para volver a realizar un episodio.
        """
        self.puntaje_total = 0
        self.puntaje_turno = 0
        self.dados = [1, 2, 3, 4, 5, 6]  # se tiran los 6 dados cuando aranca el juego
        self.termino = False  # flag para indicar si el turno termino
        self.turnos = 1

    def step(self, accion):
        """Dada una acción devuelve una recompensa.
        El estado es modificado acorde a la acción y su interacción con el ambiente.
        Podría ser útil devolver si terminó o no el turno.

        Args:
            accion: Acción elegida por un agente.

        Returns:
            tuple[int, bool]: Una recompensa y un flag que indica si terminó el turno. 
        """
        recompensa = 0 
        if accion == JUGADA_TIRAR:
            # Tirada de dados y cálculo del puntaje
            self.dados = [np.random.randint(1, 7) for _ in range(len(self.dados))]
            puntaje_tirada, dados_no_usados = puntaje_y_no_usados(self.dados)

            if puntaje_tirada == 0: 
                self.turnos += 1
                recompensa = - self.puntaje_turno * self.turnos
                self.puntaje_turno = 0
                self.termino = True

            else:
                self.puntaje_turno += puntaje_tirada
                self.dados = dados_no_usados
                recompensa = self.puntaje_turno / self.turnos

                if len(self.dados) == 0:
                    self.dados = [1, 2, 3, 4, 5, 6]

        elif accion == JUGADA_PLANTARSE:
            # El jugador se planta, se suma el puntaje del turno al total
            self.puntaje_total += self.puntaje_turno
            self.puntaje_turno = 0
            self.termino = True
            self.turnos += 1
            recompensa = -self.turnos

        return recompensa, self.termino

class EstadoDiezMil(): #me dijo chat que no deberia heredar al ambiente
    def __init__(self):
        """Definir qué hace a un estado de diez mil.
        Recordar que la complejidad del estado repercute en la complejidad de la tabla del agente de q-learning.
        """
        # ver el puntaje de ese turno y la len de dados restantes
        self.puntaje_turno = 0 #ver si gane puntaje? hacer rango? 
        self.cant_dados = 6 #cant de dados restantes 

    def actualizar_estado(self, ambiente: AmbienteDiezMil) -> None:
        """Modifica las variables internas del estado luego de una tirada.

        Args:
            ambiente (AmbienteDiezMil): El ambiente actual para obtener el estado real.
        """
        self.puntaje_turno = ambiente.puntaje_turno
        self.cant_dados = len(ambiente.dados)  # reflejamos la cantidad de dados restantes en el ambiente
    
    def fin_turno(self):
        """Modifica el estado al terminar el turno.
        """
        self.puntaje_turno = 0
        self.cant_dados = 6

    def __str__(self):
        """Representación en texto de EstadoDiezMil.
        Ayuda a tener una versión legible del objeto.

        Returns:
            str: Representación en texto de EstadoDiezMil.
        """
        return f"Puntaje Turno: {self.puntaje_turno}, Dados Restantes: {self.cant_dados}"

class AgenteQLearning(EstadoDiezMil):
    def __init__(
        self,
        ambiente: AmbienteDiezMil,
        alpha: float,
        gamma: float,
        epsilon: float,
        *args,
        **kwargs
    ):
        """Definir las variables internas de un Agente que implementa el algoritmo de Q-Learning.

        Args:
            ambiente (AmbienteDiezMil): Ambiente con el que interactuará el agente.
            alpha (float): Tasa de aprendizaje.
            gamma (float): Factor de descuento.
            epsilon (float): Probabilidad de explorar.
        """
        self.ambiente = ambiente
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        
        self.q_table = defaultdict(float)
        for i in range (50, 20000, 50):
            for j in range(1,7):
                self.q_table[(i, j), JUGADA_TIRAR] = 0
                self.q_table[(i, j), JUGADA_PLANTARSE] = 0
        
    def elegir_accion(self, estado: EstadoDiezMil):
        """Selecciona una acción de acuerdo a una política ε-greedy.
        """
        if np.random.rand() < self.epsilon: #explorando
            if self.q_table[(estado, JUGADA_TIRAR)] > self.q_table[(estado, JUGADA_PLANTARSE)]:
                return JUGADA_PLANTARSE
            else:
                return JUGADA_TIRAR
        
        else: #explotar
            if self.q_table[(estado, JUGADA_TIRAR)] > self.q_table[(estado, JUGADA_PLANTARSE)]:
                return JUGADA_TIRAR
            elif self.q_table[(estado, JUGADA_TIRAR)] < self.q_table[(estado, JUGADA_PLANTARSE)]:
                return JUGADA_PLANTARSE
            else: 
                return JUGADA_TIRAR

    def entrenar(self, episodios: int, verbose: bool = True) -> None:
        """Dada una cantidad de episodios, se repite el ciclo del algoritmo de Q-learning.
        Recomendación: usar tqdm para observar el progreso en los episodios.

        Args:
            episodios (int): Cantidad de episodios a iterar.
            verbose (bool, optional): Flag para hacer visible qué ocurre en cada paso. Defaults to False.
        """
        for episodio in tqdm(range(episodios)):
            estado = EstadoDiezMil()
            self.ambiente.reset()

            while self.ambiente.puntaje_total < 10000:
                accion = self.elegir_accion((estado.puntaje_turno, estado.cant_dados))
                recompensa, termino= self.ambiente.step(accion)
                estado_anterior = (estado.puntaje_turno, estado.cant_dados)
                estado.actualizar_estado(self.ambiente)
                nuevo_estado = (estado.puntaje_turno, estado.cant_dados)

                if termino: # termina el turno y actualizo la tabla para un estado terminal
                    # En estado terminal, no hay S_{t+1}, por lo tanto la actualización se simplifica
                    self.q_table[(estado_anterior, accion)] += self.alpha * (recompensa - self.q_table[(estado_anterior, accion)])
                    estado.fin_turno()
                else:
                    # Estado no terminal, sigue la actualización estándar de Q-learning
                    max_q = max(self.q_table[(nuevo_estado, a)] for a in [JUGADA_PLANTARSE, JUGADA_TIRAR])
                    self.q_table[(estado_anterior, accion)] += self.alpha * (recompensa + self.gamma * max_q - self.q_table[(estado_anterior, accion)])

    def guardar_politica(self, filename: str):
        """Almacena la política del agente en un formato conveniente.

        Args:
            filename (str): Nombre/Path del archivo a generar.
        """
        politica_dict = {}
    
        # Iterar sobre todos los estados únicos y sus acciones posibles
        for estado in set(key[0] for key in self.q_table.keys()):
            # Obtener los Q-values para las acciones posibles en este estado
            q_tirar = self.q_table[(estado, JUGADA_TIRAR)]
            q_plantarse = self.q_table[(estado, JUGADA_PLANTARSE)]
            
            # Elegir la mejor acción según los Q-values
            mejor_accion = JUGADA_TIRAR if q_tirar >= q_plantarse else JUGADA_PLANTARSE ##REVISAR
            
            # Guardar la mejor acción en el diccionario
            politica_dict[str(estado)] = mejor_accion
        
        # Escribir el diccionario en un archivo JSON
        with open(filename, 'w') as file:
            json.dump(politica_dict, file)

class JugadorEntrenado(Jugador):
    def __init__(self, nombre: str, filename_politica: str):
        self.nombre = nombre
        self.politica = self._leer_politica(filename_politica)
        
    def _leer_politica(self, filename:str, SEP:str=','):
        """Carga una politica entrenada con un agente de RL, que está guardada
        en el archivo filename en un formato conveniente.

        Args:
            filename (str): Nombre/Path del archivo que contiene a una política almacenada. 
        """
        with open(filename, 'r') as file:
            politica = json.load(file)
        
        # Convertimos las claves de vuelta a tuplas si es necesario
        self.politica = {}
        for key, value in politica.items():
            try:
                # Convertir el string a una tupla
                estado = eval(key)
                self.politica[estado] = value
            except:
                print(f"Error al procesar la clave: {key}")

        return self.politica

    def jugar(
        self,
        puntaje_total:int,
        puntaje_turno:int,
        dados:list[int],
    ) -> tuple[int,list[int]]:
        """Devuelve una jugada y los dados a tirar.

        Args:
            puntaje_total (int): Puntaje total del jugador en la partida.
            puntaje_turno (int): Puntaje en el turno del jugador
            dados (list[int]): Tirada del turno.

        Returns:
            tuple[int,list[int]]: Una jugada y la lista de dados a tirar.
        """
        #print("Política cargada:", self.politica)

        puntaje_tirada, no_usados = puntaje_y_no_usados(dados)
        puntaje_turno += puntaje_tirada
        if len(no_usados) == 0:
            estado = (puntaje_turno, 6)
        else : 
            estado = (puntaje_turno, len(no_usados))

        # print(estado, len(no_usados), dados, no_usados)
        jugada = self.politica[estado]

        jugada = np.argmax(jugada)
        
        if jugada == 0:
            puntaje_total += puntaje_turno
            return (JUGADA_PLANTARSE, [])

        elif jugada == 1:
            return (JUGADA_TIRAR, no_usados)
        
        # puntaje, no_usados = puntaje_y_no_usados(dados)

        # COMPLETAR
        # estado = ...
        # jugada = self.politica[estado]
       
        # if jugada==JUGADA_PLANTARSE:
        #     return (JUGADA_PLANTARSE, [])
        # elif jugada==JUGADA_TIRAR:
        #     return (JUGADA_TIRAR, no_usados)