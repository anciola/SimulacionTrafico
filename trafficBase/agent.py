from mesa import Agent


class Car(Agent):
    """
    Auto
    Atributos:
        unique_id: Agent's ID
        model: modelo de simulacion
        pos: posicion actual
        direccion: direccion actual
    """
    def __init__(self, unique_id, pos, model):
        """
        Crea un nuevo coche
        Args:
            unique_id: The agent's ID
            pos: the agents position
            model: Model reference for the agent
        """
        super().__init__(unique_id, model)
        self.id = unique_id
        self.model = model
        self.pos = pos
        self.direccion = None

    def move(self, pos):
        """
        Mueve al auto a la siguiente posicion
        """
        self.model.grid.move_agent(self, pos)

    def step(self):
        """
        El Auto tiene varias opciones de movimiento
        Depende de la direccion de la calle,
        de si hay semaforos inmediatos,
        si el paso esta libre o si puede rebasar
        """

        # Lee Ubicacion actual
        this_cell = self.model.grid.get_cell_list_contents([self.pos])
        (x, y) = self.pos

        # Si se encuentra sobre una calle lee en que direccion va
        calle = [obj for obj in this_cell if isinstance(obj, Road)]
        if len(calle) != 0:
            calle = calle[0]
            # dependiendo de ella se ve posicion siguiente
            if calle.direction == "Left":
                x -= 1
                self.direccion = "Left"
            elif calle.direction == "Right":
                x += 1
                self.direccion = "Right"
            elif calle.direction == "Up":
                y += 1
                self.direccion = "Up"
            elif calle.direction == "Down":
                y -= 1
                self.direccion = "Down"

            # se checa que no exceda los limites del mapa
            if x < self.model.width and y < self.model.height:
                siguiente_posicion = (x, y)
            else:
                siguiente_posicion = self.pos

            # se checa que la posible celda siguiente
            # este vacia y no tenga semaforos
            contenidos = self.model.grid.get_cell_list_contents([siguiente_posicion])
            auto = [obj for obj in contenidos if isinstance(obj, Car)]
            semaforo = [obj for obj in contenidos
                        if isinstance(obj, Traffic_Light)]

            # si el paso es libre se da un paso
            if len(semaforo) == 0:
                if len(auto) == 0:
                    self.move(siguiente_posicion)
                # si esta ocupada la celda siguiente, el auto busca rebasar
                else:
                    vecinos = self.model.grid.get_neighborhood(
                                self.pos,
                                moore=False,
                                include_center=False)
                    for posicion in vecinos:
                        contenidos = self.model.grid.get_cell_list_contents([posicion])
                        coches = [obj for obj in contenidos
                                  if isinstance(obj, Car)]
                        calles = [obj for obj in contenidos
                                  if isinstance(obj, Road)]

                        # checa si hay autos
                        # si no los hay, se mueve lateralmente
                        if len(calles) > 0 and len(coches) == 0:
                            self.move(posicion)

            # en caso de que hubiera semaforo, se ve su color
            else:
                # si esta en verde sigue
                semaforo = semaforo[0]
                if semaforo.color:
                    self.move(siguiente_posicion)

        # en caso de encontrarse directamente sobre un semaforo
        # se sigue la direccion que tenia en el turno anterior
        semaforo = [obj for obj in this_cell
                    if isinstance(obj, Traffic_Light)]
        if len(semaforo) != 0:
            if self.direccion == "Left":
                self.move((x-1, y))
            if self.direccion == "Right":
                self.move((x+1, y))
            if self.direccion == "Up":
                self.move((x, y+1))
            if self.direccion == "Down":
                self.move((x, y-1))


class Traffic_Light(Agent):
    """
    Semaforo
    Indica si es posible cruzar.

    Atributos:
        color,
        tiempo para cambiar,
        posicion,
        autos_esperando
    """
    def __init__(self, unique_id, pos, model, color=False, timeToChange=10):
        super().__init__(unique_id, model)
        self.color = color
        self.timeToChange = timeToChange
        self.pos = pos
        self.autos_esperando = 0

    def step(self):
        """
        Se coordinan entre los de la misma interseccion
        Solo una direccion este prendida a la vez
        Se le da prioridad a direccion con mas coches
        """

        # se ubica al semaforo "hermano" (misma interseccion, misma calle)
        # esto se hace gracias a que el parametro moore es falso,
        # no se ve en celdas que estan en diagonal
        vecinos = self.model.grid.get_neighbors(self.pos, False, False, 1)
        semaforo_hermano = [obj for obj in vecinos
                            if isinstance(obj, Traffic_Light)][0]

        # se ubica a los semaforos primos (misma interseccion, otra calle)
        # ahora el parametro moore es verdadero
        # semaforos primo esta en diagonal
        vecinos2 = self.model.grid.get_neighbors(self.pos, True, False, 1)
        semaforo_primo = [obj for obj in vecinos2
                          if isinstance(obj, Traffic_Light)]

        # solo el semaforo mas cercano de la esquina detecta a un primo,
        # este es el que coordina cambios de color
        if len(semaforo_primo) == 2:
            semaforo_primo.remove(semaforo_hermano)
            semaforo_primo = semaforo_primo[0]

            # se calculan autos cercanos
            autos_cercanos = self.model.grid.get_neighbors(self.pos,
                                                           False, False, 4)
            autos_cercanos = [obj for obj in autos_cercanos
                              if isinstance(obj, Car)]
            self.autos_esperando = len(autos_cercanos)

            # si se tienen mas que los de la otra calle, se da prioridad
            if self.autos_esperando > semaforo_primo.autos_esperando:
                self.color = True
                semaforo_hermano.color = True
                semaforo_primo.color = False
            else:
                semaforo_hermano.color = self.color
        else:
            pass


class Destination(Agent):
    """
    Destino
    Genera y absorbe autos aleatoriamente.

    Atributos:
        recien_creo,
        modelo,
        id
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.recien_creo = False
        self.model = model
        self.id = unique_id

    def step(self):
        """
        En cada paso el destino tiene probabilidad
        de generar un coche si la calle esta vacia
        o de absorber un coche que se acerque
        """

        # obtiene estado de calles vecinas
        vecinos = self.model.grid.get_neighborhood(
            self.pos,
            moore=False,
            include_center=False)

        for posicion in vecinos:
            contenidos = self.model.grid.get_cell_list_contents([posicion])
            # checa si hay autos, calles
            coches = [obj for obj in contenidos if isinstance(obj, Car)]
            calles = [obj for obj in contenidos if isinstance(obj, Road)]
            flip = self.random.choice([0, 0, 0, 0, 1])

            # si si hay un coche:
            if len(coches) > 0:
                # si 0 / 1 -> quita o no ese coche
                if not flip:
                    print('un auto ha llegado a su destino en ' +
                          str(posicion))
                    car = self.random.choice(coches)
                    self.model.grid.remove_agent(car)
                    self.model.schedule.remove(car)

            # si estan vacias:
            elif len(calles) > 0:
                # si 0 / 1 -> genera o no un coche
                if flip:
                    print('un auto se ha incorporado al trafico en' +
                          str(posicion))
                    car = Car(self.model.next_id(), posicion, self.model)
                    self.model.grid.place_agent(car, posicion)
                    self.model.schedule.add(car)
                    self.recien_creo = True


class Obstacle(Agent):
    """
    Obstaculo
    Representa edificios.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass


class Road(Agent):
    """
    Calle
    Los autos se mueven sobre ellas.

    Atributos:
        direccion,
        modelo
    """
    def __init__(self, unique_id, model, direction="Left"):
        super().__init__(unique_id, model)
        self.direction = direction
        self.model = model

    def step(self):
        pass
