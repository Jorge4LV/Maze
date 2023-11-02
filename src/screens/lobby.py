import re
import time
import asyncio
import discohook
import numpy as np
from ..utils.constants import COLOR_GREEN, COLOR_ORANGE, COLOR_RED, MAX_PLAYERS, COLOR_BLURPLE
from .maze import MazeView

async def is_host(interaction):
  if not interaction.from_originator:
    await interaction.response.send('Denied because you are not the host!', ephemeral = True)
    return False
  return True

@discohook.button.new('Start', emoji = '🏁', style = discohook.ButtonStyle.green, custom_id = 'start:v0.0')
async def start_button(interaction):
  embed = interaction.message.embeds[0]

  embed.title = 'Maze Race Starting...'
  embed.description = '\n'.join([
    '{} has started the maze game! Get ready...'.format(interaction.message.interaction.user.mention),
    '(Generating a maze, takes 1-20 seconds depending on the size)'
  ])
  embed.color = COLOR_ORANGE

  response = await interaction.response.update_message(embed = embed, view = None)

  app = interaction.client
  helpers = app.helpers

  level = int(embed.fields[0]['value'].split('\n')[0].split(' ')[-1][:-1].strip('`')) # parse it out
  player_ids = re.sub('<|@|!|>', '', embed.fields[1]['value']).split() # ! is lib issue

  maze_id, m = helpers.generate_maze(level)

  grid = (1 - m.grid) * 255 # invert colors, 0 = black, 1 = white
  grid = np.repeat(grid[:, :, np.newaxis], 3, axis = 2) # triple the cells to become R,G,B
  grid[m.start[0], m.start[1]] = (255, 255, 0) # start = YELLOW
  grid[m.end[0], m.end[1]] = (0, 255, 0) # end = GREEN

  app.mazes[maze_id] = await asyncio.to_thread(helpers.draw_maze(grid))

  await response.followup('maze')

  # cache maze data
  # app.mazes[maze_id] = 
  # app.mazes[maze_id] = helpers.draw_maze(maze_grid)

  """grid = grid.astype(object) # convert inner tuples to list
  
  for y, row in enumerate(grid):
    for x, cell in enumerate(row):
      grid[y, x] = cell, cell, cell"""

  # print('after grid combat', grid)
  # print('alt', new_grid)
  

  """timeout = int(time.time() + level_to_seconds(level))

  await app.db.create_maze(maze_id, m.grid.flatten(), m.start, m.end, timeout, response.inter.token, player_ids)

  print(m)
  print('tw', grid)
  
  # draw the maze
  print(maze_grid)
  app.mazes[maze_id] = helpers.draw_maze(maze_grid)

  async def prepare_mazes(user_id): # fetch user avatars and generates maze images first
    user = app.users.get(int(user_id))
    if not user: # function reloaded
      user = await app.fetch_user(user_id)
    content = user.mention
    embed = discohook.Embed(
      '{}\'s Maze'.format(user), # global or old/new username
      description = '\n'.join([
        'You have <t:{}:R> to get through the maze.'.format(timeout),
        'Click the buttons to move. Good luck!'
      ]),
      color = COLOR_BLURPLE
    )
    embed.set_image('attachment://maze.png')
    image = await asyncio.to_thread(helpers.draw_maze, maze_id, user)
    return content, embed, image

  results = await asyncio.gather(*[prepare_mazes(user_id) for user_id in player_ids])
  
  await asyncio.gather(*[ # sends altogether afterwards so everyone starts somewhat at the same time
    MazeView(response, data = (maze_id, content, embed, image)).followup() 
    for content, embed, image in results
  ])"""
start_button.checks.append(is_host)

@discohook.button.new('Join', emoji = '🚪', custom_id = 'join:v0.0')
async def join_button(interaction):
  embed = interaction.message.embeds[0]
  text = embed.fields[1]['value']

  if interaction.author.id in text: # text is players embed field value
    return await interaction.response.send('You are already in the game.', ephemeral = True)
  elif len(text.split(' ')) == MAX_PLAYERS: # player count
    return await interaction.response.send('Can\'t join, maximum players reached ({}).'.format(MAX_PLAYERS))

  text += ' ' + interaction.author.mention # add their mention to text

  embed.fields.pop() # update the players field
  embed.add_field(
    'Players ({})'.format(len(text.split(' '))),
    text,
    inline = True
  )

  interaction.client.users[int(interaction.author.id)] = interaction.author

  await LobbyView(interaction, 1, data = embed).update()

@discohook.button.new('Cancel', emoji = '🏳️', style = discohook.ButtonStyle.red, custom_id = 'cancel:v0.0')
async def cancel_button(interaction):
  embed = interaction.message.embeds[0]
  embed.color = COLOR_RED
  embed.set_footer('Game was cancelled by the host.')
  await interaction.response.update_message(embed = embed, view = None)
cancel_button.checks.append(is_host)

class LobbyView(discohook.View):
  def __init__(self, interaction = None, flag = None, data = None):
    super().__init__()

    if interaction:
      self.interaction = interaction

      if not flag: # start (used /maze)

        self.embed = discohook.Embed(
          'Maze Lobby',
          description = '\n'.join([
            'A new maze race is being hosted by {}.'.format(interaction.author.mention),
            'Everyone else click **Join** to join!',
            'When everyone is ready, tell the host to press **Start** to start.'
          ]),
          color = COLOR_GREEN
        )
        
        level = data
        helpers = interaction.client.helpers
        size = helpers.level_to_size(level)
        seconds = helpers.level_to_seconds(level)

        self.embed.add_field(
          'Details',
          '\n'.join([
            'Level: `{}`'.format(level),
            'Size: `{0}x{0}`'.format(size),
            'Time: `{}s`'.format(seconds)
          ]),
          inline = True
        )

        self.embed.add_field('Players (1)', interaction.author.mention, inline = True)

        self.add_buttons(start_button, join_button, cancel_button)

      elif flag == 1: # update lobby (someone successfully clicked Join)

        self.embed = data

        self.add_buttons(start_button, join_button, cancel_button)
          
      elif flag == 2: # started (host clicked Start)
        pass
      elif flag == 3: # finished (everyone finished playing/timed out)
        pass
      else:
        raise ValueError('Unhandled LobbyView flag', flag)

    else: # persistent view
      self.add_buttons(start_button, join_button, cancel_button)
  
  async def send(self):
    await self.interaction.response.send(embed = self.embed, view = self)

  async def update(self):
    await self.interaction.response.update_message(embed = self.embed, view = self)