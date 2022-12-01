from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from agent import *
import json


class Modelo(Model):
    """
    Crea la simulacion del tráfico.
    Args:
        N: Number of agents in the simulation
        height, width: The size of the grid to model
    """
    def __init__(self):

        self.current_id = 0

        dataDictionary = json.load(open("mapDictionary.txt"))

        with open('base2022.txt') as baseFile:
            lines = baseFile.readlines()
            self.width = len(lines[0])-1
            self.height = len(lines)

            self.grid = MultiGrid(self.width, self.height, torus=False)
            self.schedule = RandomActivation(self)

            for r, row in enumerate(lines):
                for c, col in enumerate(row):

                    # Se Colocan Calles
                    if col in ["v", "^", ">", "<"]:
                        agent = Road(f"r{r*self.width+c}", self,
                                     dataDictionary[col])
                        self.grid.place_agent(agent, (c, self.height - r - 1))

                    # Se Colocan Semaforos
                    elif col in ["S", "s"]:
                        agent = Traffic_Light(f"tl{r*self.width+c}",
                                              (c, self.height - r - 1),
                                              self,
                                              False if col == "S" else True,
                                              int(dataDictionary[col]))
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                        self.schedule.add(agent)

                    # Se Colocan Obstaculos
                    elif col == "#":
                        agent = Obstacle(f"ob{r*self.width+c}", self)
                        self.grid.place_agent(agent, (c, self.height - r - 1))

                    # Se Colocan Destinos
                    elif col == "D":
                        agent = Destination(f"d{r*self.width+c}", self)
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                        self.schedule.add(agent)

#        self.num_agents = N
        self.running = True

    def step(self):
        '''Avanza el modelo un paso'''
        self.schedule.step()
        if self.schedule.steps % 10 == 0:
            for agents, x, y in self.grid.coord_iter():
                for agent in agents:
                    if isinstance(agent, Traffic_Light):
                        agent.color = not agent.color