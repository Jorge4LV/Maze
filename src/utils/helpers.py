"""
Code that might be reused in other places or just odd.
"""

import io
import math
import string
import asyncio
import mazelib
import discohook
import numpy as np
from mazelib.generate.Prims import Prims
from mazelib.solve.BacktrackingSolver import BacktrackingSolver
from PIL import Image
from .constants import TIME_LIMIT_BASE, TIME_LIMIT_THRESHOLD, IMAGE_SIZE

blocked_pattern = np.array([
  [0, 1, 0, 0, 0],
  [0, 1, 0, 1, 1],
  [0, 0, 0, 0, 0],
  [1, 1, 0, 1, 0],
  [0, 0, 0, 1, 0]
])

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

def generate_maze(level): # blocking
  size = level + 2
  m = mazelib.Maze()
  m.generator = Prims(size, size)
  m.solver = BacktrackingSolver()
  while True:
    m.generate_monte_carlo(10, 3, 1.0)
    # ^ this essentially generates 10 mazes, with 3 different entrances = 30 variations, and picks the hardest one
    # thats solely the reason why its slow, decrease those values to make it faster

    # prevents level 1 from generating "that" pattern
    if level != 1 or not np.array_equal(m.grid[1:6, 1:6], blocked_pattern): 
      break
  return m

def draw_maze(flat_grid, start, end, image_size): # blocking, returns 2d grid and PIL.Image
  size = int(math.sqrt(len(flat_grid))) # starts as flattened so we can reuse this from db
  maze_grid = flat_grid.reshape((size, size)) # unflatten it
  maze_grid[start] = 0 # makes start and end pathway tiles, by default they're walls
  maze_grid[end] = 0

  image_grid = (1 - maze_grid) * 255 # invert mazelib's numbers to be 0 = black, 1 = white
  image_grid = np.repeat(image_grid[:, :, np.newaxis], 3, axis = 2) # triple the cells to become R,G,B
  image_grid[start] = (255, 255, 0) # start = YELLOW
  image_grid[end] = (0, 255, 0) # end = GREEN
  
  maze_image = Image.fromarray(image_grid.astype(np.uint8)) # this blocks
  maze_image = maze_image.resize((image_size, image_size), Image.Resampling.NEAREST) # so does this
  
  return maze_grid, maze_image

async def draw_player_on_maze(app, maze_data, position, user, level, image_size): # async to fetch user avatar
  maze_grid, maze_image = maze_data

  factor = image_size/len(maze_grid) # size of 1 tile in pixels
  print('this factor', factor)

  # fetch user background if not cached
  key = '{}:{}:{}'.format(user.id, level, image_size) # can reuse avatar for same levels somewhere else
  user_image = app.avatars.get(key)
  if not user_image:
    if user.avatar.default:
      user_image = await asyncio.to_thread(Image.open, 'src/assets/{}.png'.format(user.avatar.hash))
    else:
      size = get_power_of_2(round(factor)) # avatar png sizes can only be in powers of 2
      url = '.'.join(str(user.avatar).split('.')[:-1]) + '.png?size=' + str(size)
      async with app.session.get(url) as resp:
        if resp.status != 200:
          raise ValueError('Fetch avatar returned bad status', resp.status)
        user_image = await asyncio.to_thread(Image.open, io.BytesIO(await resp.read()))
    size = round(factor * 0.8) # avatar image is slightly smaller than a tile on the map
    user_image = await asyncio.to_thread(user_image.resize, (size, size), Image.Resampling.NEAREST)
    app.avatars[key] = user_image
  
  def blocking():    
    # make copy of maze background
    im = maze_image.copy()

    # paste user image onto maze background image, offset at the given position (y, x) mazelib -> (x, y) pillow paste 
    im.paste(user_image, tuple(round(i * factor + factor * 0.1) for i in reversed(position))) # 0.1 is cuz of 0.8 adjustment

    # save
    buffer = io.BytesIO()
    im.save(buffer, 'PNG')
    return buffer
  
  # return as file object
  buffer = await asyncio.to_thread(blocking)
  return discohook.File('maze.png', content = buffer.getvalue())