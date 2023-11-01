import asyncio
import mazelib
from mazelib.generate.Prims import Prims
from mazelib.solve.BacktrackingSolver import BacktrackingSolver
from .constants import TIME_LIMIT_BASE, TIME_LIMIT_THRESHOLD

def level_to_size(level):
  return (level + 2) * 2 + 1

def level_to_seconds(level):
  if level > TIME_LIMIT_THRESHOLD:
    return TIME_LIMIT_BASE + 5 * 2
  return TIME_LIMIT_BASE

def generate_maze(size): # this is blocking
  m = mazelib.Maze()
  m.generator = Prims(size, size)
  m.solver = BacktrackingSolver()
  m.generate_monte_carlo(10, 3, 1.0) 
  # ^ this essentially generates 10 mazes, with 3 different entrances = 30 variations, and picks the hardest one
  # thats solely the reason why its slow, decrease those values to make it faster
  return m