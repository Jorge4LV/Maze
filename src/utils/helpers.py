"""
Code that might be reused in other places or just odd.
"""

import io
import math
import asyncio
import mazelib
import discohook
import numpy as np
from mazelib.generate.Prims import Prims
from mazelib.solve.BacktrackingSolver import BacktrackingSolver
from PIL import Image, ImageOps
from .constants import TIME_LIMIT_BASE, TIME_LIMIT_THRESHOLD, IMAGE_SIZE
import string
import random

def level_to_size(level):
  return (level + 2) * 2 + 1

def level_to_seconds(level):
  if level > TIME_LIMIT_THRESHOLD:
    return TIME_LIMIT_BASE + 5 * (level - TIME_LIMIT_THRESHOLD)
  return TIME_LIMIT_BASE

def get_power_of_2(n): # 147 becomes 256
  i = 2
  while True:
    if i >= n:
      return i
    i *= 2

def generate_maze_id(): # returns a unique 16 letter string
  chars = tuple(string.ascii_letters + string.digits + '-_')
  return ''.join(random.choice(chars) for _ in range(16))

def generate_maze(level): # this is blocking
  size = level + 2
  m = mazelib.Maze()
  m.generator = Prims(size, size)
  m.solver = BacktrackingSolver()
  m.generate_monte_carlo(10, 3, 1.0) 
  # ^ this essentially generates 10 mazes, with 3 different entrances = 30 variations, and picks the hardest one
  # thats solely the reason why its slow, decrease those values to make it faster
  return generate_maze_id(), m

async def draw_maze(flat_grid, start, end): # returns 2d grid and PIL.Image
  size = int(math.sqrt(len(flat_grid))) # starts as flattened so we can reuse this from db
  maze_grid = flat_grid.reshape((size, size)) # unflatten it
  maze_grid[start] = 0 # makes start and end pathway tiles, by default they're walls
  maze_grid[end] = 0

  image_grid = (1 - maze_grid) * 255 # invert mazelib's numbers to be 0 = black, 1 = white
  image_grid = np.repeat(image_grid[:, :, np.newaxis], 3, axis = 2) # triple the cells to become R,G,B
  image_grid[start] = (255, 255, 0) # start = YELLOW
  image_grid[end] = (0, 255, 0) # end = GREEN
  
  maze_image = Image.fromarray(image_grid.astype(np.uint8))
  maze_image = await asyncio.to_thread(maze_image.resize, (IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.NEAREST)
  return maze_grid, maze_image

async def draw_player_on_maze(app, maze_data, position, user, level):
  maze_grid, maze_image = maze_data

  factor = IMAGE_SIZE/len(maze_grid) # size of 1 tile in pixels

  # fetch user background if not cached
  key = '{}:{}'.format(user.id, level) # can reuse avatar for same levels somewhere else
  user_image = app.avatars.get(key)
  if not user_image:
    size = get_power_of_2(round(factor)) # avatar png sizes can only be in powers of 2
    url = '.'.join(str(user.avatar).split('.')[:-1]) + '.png?size=' + str(size)
    async with app.session.get(url) as resp:
      if resp.status != 200:
        raise ValueError('Fetch avatar returned bad status', resp.status)
      user_image = Image.open(io.BytesIO(await resp.read()))
    size = round(factor * 0.8) # avatar image is slightly smaller than a tile on the map
    user_image = await asyncio.to_thread(user_image.resize, (size, size), Image.Resampling.NEAREST)
    app.avatars[key] = user_image
  
  # make copy of maze background
  im = maze_image.copy()

  # paste user image onto maze background image, offset at the given position (y, x) mazelib -> (x, y) pillow paste 
  im.paste(user_image, tuple(round(i * factor + factor * 0.1) for i in reversed(position))) # 0.1 is cuz of 0.8 adjustment

  # return as file object
  buffer = io.BytesIO()
  im.save(buffer, 'PNG')
  buffer.seek(0) # have to do this or it doesn't load the file
  return discohook.File('maze.png', content = buffer.read())
