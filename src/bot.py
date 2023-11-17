"""
Starts running the bot.
"""

import os
import json
import asyncio
import datetime
import traceback
import contextlib
import aiohttp
import discohook
from starlette.responses import Response, PlainTextResponse
from .utils.database import Database
from .utils import constants, helpers
from .cogs.ping import ping_command
from .cogs.maze import maze_command
from .cogs.stats import stats_command
from .cogs.top import top_command
from .screens.lobby import LobbyView
from .screens.maze import MazeView
from .screens.top import TopView

def run():
  
  # Lifespan to attach extra .session and .db attributes, cancel + shutdown is for local testing
  @contextlib.asynccontextmanager
  async def lifespan(app):
    async with aiohttp.ClientSession() as app.session:
      async with Database(app, os.getenv('SPACE_DATA_KEY')) as app.db:
        try:
          yield
        except asyncio.CancelledError:
          print('Ignoring cancelled error. (CTRL+C)')
        else:
          print('Closed without errors.')
        finally:
          await app.http.session.close() # close bot session

  # Define the bot
  app = discohook.Client(
    application_id = os.getenv('DISCORD_APPLICATION_ID'),
    public_key = os.getenv('DISCORD_PUBLIC_KEY'),
    token = os.getenv('DISCORD_BOT_TOKEN'),
    password = os.getenv('SYNC_PASSWORD'),
    lifespan = lifespan
  )

  # Attach error handler
  app.errors = []
  error_log_webhook = discohook.PartialWebhook.from_url(app, os.getenv('ERROR_LOG_WEBHOOK'))
  @app.on_interaction_error()
  async def on_error(interaction, error):
    if isinstance(error, discohook.errors.CheckFailure):
      return print('Ignoring check failure', str(interaction.author), interaction.data['custom_id'].split(':')[0])
    if interaction.responded:
      await interaction.response.followup('Sorry, an error has occured.')
    else:
      await interaction.response.send('Sorry, an error has occured (after responding).')
    trace = tuple(traceback.TracebackException.from_exception(error).format())
    app.errors.append(trace)
    text = ''.join(trace)
    print(text)
    await error_log_webhook.send(text[:2000])
  
  # Set custom ID parser
  @app.custom_id_parser()
  async def custom_id_parser(interaction, custom_id): # interaction is unused
    return ':'.join(custom_id.split(':')[:2]) # name:v0.0 returned

  # Add world record log webhook
  app.wr_log_webhook = discohook.PartialWebhook.from_url(app, os.getenv('WR_LOG_WEBHOOK'))

  # Attach helpers and constants, might be useful
  app.constants = constants
  app.helpers = helpers

  # Attach bot caches
  app.mazes = {} # maze_id : (2d maze grid, maze image)
  app.users = {} # user_id : User/Member, saves time when starting the race & updating highscores / skip user fetch
  app.avatars = {} # user_id:level : user images scaled proportionally for that maze level
  app.stats = {} # userid : {level:timetaken}, read only, used for stats command
  app.tops = {} # level : [(userid, name, timetaken, timestamp), ...], used for top command

  # Set bot started at timestamp
  app.started_at = datetime.datetime.utcnow()

  # Set if bot is test or not
  app.test = bool(os.getenv('test'))

  # Add commands
  app.add_commands(
    ping_command,
    maze_command,
    stats_command,
    top_command
  )

  # Load persistent views/components  
  app.load_components(LobbyView())
  app.load_components(MazeView())
  app.load_components(TopView())

  # Attach / route for debugging
  @app.route('/', methods = ['GET'])
  async def root(request):
    return PlainTextResponse(
      '\n'.join([
        'Started: {}'.format(app.started_at),
        '',
        'Test: {}'.format(app.test),
        '',
        'Cache: {}'.format(json.dumps({
          'Mazes' : app.mazes,
          'Users' : app.users,
          'Avatars' : app.avatars,
          'Stats' : app.stats,
          'Tops' : app.tops
        }, indent = 2, default = repr)),
        '',
        'Errors: {}'.format(json.dumps(app.errors, indent = 2)),
      ])
    )

  # Actions handler
  @app.route('/__space/v0/actions', methods = ['POST'])
  async def actions(request):
    data = await request.json()
    event = data['event']
    if event['id'] == 'check':
      await app.db.end_timed_out_mazes()
    return Response()

  # Return app object
  return app