"""
Starts running the bot.
"""

import os
import json
import asyncio
import datetime
import traceback
import contextlib
import discohook
from starlette.responses import PlainTextResponse
from .utils.database import Database
from .cogs.ping import ping_command
from .cogs.maze import maze_command
from .screens.lobby import LobbyView

def run():
  
  # Lifespan to attach extra .db attribute, cancel + shutdown is for local testing
  @contextlib.asynccontextmanager
  async def lifespan(app):
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
    return custom_id

  # Set bot started at timestamp
  app.started_at = datetime.datetime.utcnow()

  # Set if bot is test or not
  app.test = bool(os.getenv('test'))

  # Add commands
  app.add_commands(
    ping_command,
    maze_command
  )

  # Load persistent views/compoennts  
  app.load_components(LobbyView())


  # Attach / route for debugging
  @app.route('/', methods = ['GET'])
  async def root(request):
    return PlainTextResponse(
      '\n'.join([
        'Started: {}'.format(app.started_at),
        '',
        'Test: {}'.format(app.test),
        '',
        'Errors: {}'.format(json.dumps(app.errors, indent = 2)),
        '',
      ])
    )

  # Return app object
  return app