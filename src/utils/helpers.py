import asyncio
import mazelib
import discohook
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
    return TIME_LIMIT_BASE + 5 * 2
  return TIME_LIMIT_BASE

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

def draw_maze(grid): # blocking, returns PIL.Image
  size = len(grid)
  grid = grid.reshape(-1, grid.shape[-1]) # becomes [(0, 0, 0), (255, 255, 255), ...]
  print(grid)
  maze_image = Image.new('RGB', (size, size))
  maze_image.putdata(grid)
  maze_image = maze_image.rotate(90) # adjust since pil draws from top left
  maze_image = ImageOps.flip(maze_image)
  maze_image = maze_image.resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.NEAREST)
  maze_grid = m.grid # the grid to calculate player movements on
  maze_grid[m.start] = 0 # makes start and end pathway tiles, by default they're walls
  maze_grid[m.end] = 0
  return maze_grid, maze_image

  """  # draw maze background first if not cached
    maze = app.mazes.get(maze_id)
    if not maze:
      # fetch maze grid if not cached
      maze_grid = app.    
  """

  # fetch user background if not cached

  # merge them onto each other

  # return file object
  # discohook.File('maze.png', content = bytes)

  
  # # make copy of maze background
  # im = maze_image.copy()

  # # paste user image on background at specific coords
  # im.paste(user_image, tuple(int(round(i * factor + factor * 0.1)) for i in position))

  # # upload to our cdn and return the url
  # buffer = io.BytesIO()
  # im.save(buffer, 'PNG')
  # channel = bot.get_channel(CDN_CHANNEL)
  # if not channel:
  #   channel = await bot.fetch_channel(CDN_CHANNEL)
  # buffer.seek(0)
  # message = await channel.send(file = discord.File(fp = buffer, filename = 'maze.png'))
  # return message.attachments[0].url

def draw_player_on_maze(maze_im): # blocking, returns discohook.File
  pass
