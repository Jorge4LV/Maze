import time
import discohook
from deta import Deta, Query, Record, Updater
from .constants import COLOR_GREEN

class Database(Deta):
  def __init__(self, app, key):
    super().__init__(key)
    self.app = app
    self.mazes = self.base('mazes')

  async def create_maze(self, maze_id, grid, start, end, timeout, token, token_expires_at, player_ids):
    data = {
      'grid' : grid,
      'start' : start,
      'end' : end,
      'timeout' : timeout,
      'token' : token, # to do Maze results followup
      'token_expires_at' : token_expires_at
    }

    for user_id in player_ids:
      data[user_id] = None # None = DQed, otherwise time taken

    record = Record(maze_id, **data)

    await self.mazes.insert(record)

  async def get_maze(self, maze_id): # server reloaded or check maze status
    query = Query()
    query.equals('key', maze_id)
    results = (await self.mazes.fetch([query]))['items']
    if results:
      return results[0]

  async def update_maze(self, maze_id, player_id, time_taken): # someone won, time_taken = 0 = gave up
    updater = Updater()
    updater.set(player_id, time_taken)
    await self.mazes.update(maze_id, updater) # errors if doesn't exist
    await self.check_maze_finished(maze_id) # send maze results screen if it finished

  async def end_maze(self, record):
    await self.mazes.delete(record['key'])

    if time.time() > record['token_expires_at']: # followup token expired, can't send maze results, rare
      return

    embed = discohook.Embed(
      'Times up! Maze Results:',
      description = '\n'.join([
        '{}. <@{}> - {}'.format(i + 1, user_id, '`{}s`'.format(time_taken) if time_taken else 'FAILED!')
        for i, (user_id, time_taken) in enumerate(sorted((
          (k, v)
          for k, v in record.items()
          if k.isdigit()
        ), key = lambda x: x[1] if x[1] else float('inf')))
      ]),
      color = COLOR_GREEN
    )

    interaction = discohook.Interaction(self.app, {'application_id' : self.app.application_id, 'token' : record['token']}) # partial interaction
    await interaction.response.followup(embed = embed) 

  async def check_maze_finished(self, maze_id): # checks if maze that maze timed out or all players finished
    record = await self.get_maze(maze_id)
    if record: # exists
      if time.time() > record['timeout'] or \
      all(
        bool(record[key]) or record[key] == 0 # won or gave up
        for key in record
        if key.isdigit()
      ):
        await self.end_maze(record)

  async def end_timed_out_mazes(self): # used for scheduled actions, has at most a 1 min delay
    query = Query()
    query.less_than('timeout', int(time.time()))
    results = (await self.mazes.fetch([query]))['items']
    for record in results:
      await self.end_maze(record)