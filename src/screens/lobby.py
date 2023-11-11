import re
import time
import asyncio
import discohook
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

  await interaction.response.update_message(embed = embed, view = None)

  level = int(embed.fields[0]['value'].split('\n')[0].split(' ')[-1][:-1].strip('`')) # parse it out
  player_ids = re.sub('<|@|!|>', '', embed.fields[1]['value']).split() # ! is lib issue

  app = interaction.client
  helpers = app.helpers

  maze_id, m = await asyncio.to_thread(helpers.generate_maze, level)

  maze_data = await helpers.draw_maze(m.grid.flatten(), m.start, m.end)
  app.mazes[maze_id] = maze_data

  seconds = helpers.level_to_seconds(level)

  async def prepare_mazes(user_id): # fetch user avatars and generates maze images first
    user = app.users.get(int(user_id))
    if not user: # server reloaded
      user = await app.fetch_user(user_id)
      app.users[int(user_id)] = user
    embed = discohook.Embed(
      '{}\'s Maze'.format(user), # global or old/new username
      description = '\n'.join([
        'You have `{}s` to get through the maze.'.format(seconds),
        'Click the buttons to move. Good luck!'
      ]),
      color = COLOR_BLURPLE
    )
    image = await helpers.draw_player_on_maze(app, maze_data, m.start, user, level)
    embed.set_image(image)
    return user_id, embed

  results = await asyncio.gather(*[prepare_mazes(user_id) for user_id in player_ids])
  
  timeout = int(time.time() + seconds)
  token_expires_at = int(interaction.created_at + 60 * 15)
  await app.db.create_maze(maze_id, m.grid.flatten().tolist(), level, m.start, m.end, timeout, interaction.token, token_expires_at, player_ids)
  
  await asyncio.gather(*[ # sends altogether afterwards so everyone starts somewhat at the same time
    MazeView(interaction, data = (maze_id, m.start, m.end, timeout, level, user_id, embed)).followup() 
    for user_id, embed in results
  ])
start_button.checks.append(is_host)

@discohook.button.new('Join', emoji = '🚪', custom_id = 'join:v0.0')
async def join_button(interaction):
  embed = interaction.message.embeds[0]
  text = embed.fields[1]['value']

  if interaction.author.id in text: # text is players embed field value
    return await interaction.response.send('You are already in the game.', ephemeral = True)
  elif len(text.split(' ')) > MAX_PLAYERS - 1: # player count
    return await interaction.response.send('Can\'t join, maximum players reached ({}).'.format(MAX_PLAYERS))

  text += ' ' + interaction.author.mention # add their mention to text

  embed.fields.pop() # update the players field
  embed.add_field(
    'Players ({})'.format(len(text.split(' '))),
    text,
    inline = True
  )

  interaction.client.users[int(interaction.author.id)] = interaction.author

  await interaction.response.update_message(embed = embed)

@discohook.button.new('Cancel', emoji = '🏳️', style = discohook.ButtonStyle.red, custom_id = 'cancel:v0.0')
async def cancel_button(interaction):
  embed = interaction.message.embeds[0]
  embed.color = COLOR_RED
  embed.set_footer('Game was cancelled by the host.')
  await interaction.response.update_message(embed = embed, view = None)
cancel_button.checks.append(is_host)

class LobbyView(discohook.View):
  def __init__(self, interaction = None, level = None):
    super().__init__()

    if interaction:
      self.interaction = interaction

      self.embed = discohook.Embed(
        'Maze Lobby',
        description = '\n'.join([
          'A new maze race is being hosted by {}.'.format(interaction.author.mention),
          'Everyone else click **Join** to join!',
          'When everyone is ready, tell the host to press **Start** to start.'
        ]),
        color = COLOR_GREEN
      )
        
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

    else: # persistent view
      self.add_buttons(start_button, join_button, cancel_button)
  
  async def send(self):
    await self.interaction.response.send(embed = self.embed, view = self)

  async def update(self):
    await self.interaction.response.update_message(embed = self.embed, view = self)