import time
import asyncio
import discohook
from deta import Deta, Query, Record, Updater
from .constants import COLOR_GREEN, MAX_LEVELS

class Database(Deta):
  def __init__(self, app, key):
    super().__init__(key)
    self.app = app
    self.mazes = self.base('mazes')
    self.stats = self.base('stats')

  async def create_maze(self, maze_id, grid, level, start, end, timeout, token, token_expires_at, player_ids):
    data = {
      'grid' : grid,
      'level' : level,
      'start' : start,
      'end' : end,
      'timeout' : timeout,
      'token' : token # to do Maze results followup
    }

    for user_id in player_ids:
      data[user_id] = None # None = DQed, otherwise time taken

    # automatically clears records after 15 mins (interaction followup timelimit)
    record = Record(maze_id, expires_at = token_expires_at, **data)

    await self.mazes.insert(record)

  async def get_maze(self, maze_id): # server reloaded or check maze status
    query = Query()
    query.equals('key', maze_id)
    records = (await self.mazes.fetch([query], limit = 1))['items']
    if records:
      return records[0]

  async def update_maze(self, maze_id, player_id, time_taken): # someone won, time_taken = 0 = gave up
    updater = Updater()
    updater.set(player_id, time_taken)
    await self.mazes.update(maze_id, updater) # errors if doesn't exist
    await self.check_maze_finished(maze_id) # send maze results screen if it finished

  async def end_maze(self, record):
    await self.mazes.delete(record['key'])

    scores = dict(sorted(  # userid (str) : score (int), score is in 0.01s
      (
      (k, v)
      for k, v in record.items()
      if k.isdigit()
      ),
      key = lambda x: x[1] if x[1] else float('inf')
    ))

    token = record['token']
    level = record['level']

    # calculate new personal/world high scores
    winner_scores = {
      user_id : time_taken
      for user_id, time_taken in scores.items()
      if time_taken # only if they won / none = didn't finish / 0 = gave up
    }
    new_pb_scores = {} # beat their personal best
    new_top_scores = {} # top 2-10
    new_wr_score = None # top 1

    if winner_scores: # if some one beat the maze, check for new pbs

      queries = []
      for user_id in winner_scores:
        query = Query()
        query.equals('user_id', user_id)
        query.equals('level', level)
        queries.append(query)
        
      records = {
        record['user_id'] : record
        for record in (await self.stats.fetch(queries))['items']
      }

      new_pb_scores = {
        user_id : time_taken
        for user_id, time_taken in winner_scores.items()
        if user_id not in records # if they never had a previous score = new pb
        or winner_scores[user_id] < records[user_id]['time_taken'] # they beat their previous score = new pb
      }

      if new_pb_scores: # if new pbs exist, update them and check for new wrs

        # due to sorting logic, records needs to be deleted and created again instead of just updating it
        keys = {
          records[user_id]['key'] : user_id
          for user_id in new_pb_scores
          if user_id in records # cant delete a record if they never had a previous score
        }

        async def get_name(user_id): # purely so leaderboards is readable
          user = self.app.users.get(int(user_id))
          if not user: # server reloaded
            user = await self.app.fetch_user(user_id)
            self.app.users[int(user_id)] = user
          return user_id, user.name if user.discriminator == 0 else '{}#{}'.format(user.name, user.discriminator)

        names = dict(await asyncio.gather(*[
          get_name(user_id)
          for user_id in new_pb_scores
        ]))

        new_keys = { # time_taken:level:userid, also assumes 99999 can be the max time, 90k = 15 mins
          '{}:{}:{}'.format(str(time_taken).zfill(5), level, user_id) : (user_id, time_taken) 
          for user_id, time_taken in new_pb_scores.items()
        }

        now = int(time.time())
        records = [
          Record(
            key,
            level = level,
            user_id = user_id,
            name = names[user_id],
            time_taken = time_taken,
            timestamp = now
          )
          for key, (user_id, time_taken) in new_keys.items()
        ]

        await asyncio.gather(
          *[
            self.stats.delete(key) 
            for key in keys
          ], 
          self.stats.put(*records)
        )

        # update stats cache if user ids are in it
        for user_id, time_taken in new_pb_scores.items():
          if user_id in self.app.stats:
            self.app.stats[user_id][level] = (time_taken, now)
        
        # check for new top 10s or world records, which means if that record key is the top 10 score
        query = Query()
        query.equals('level', level)
        records = (await self.stats.fetch([query], limit = 10))['items']

        # leaderboards wont be empty due to inserting records in it just now
        if records[0]['key'] in new_keys:
          new_wr_score = new_keys[records[0]['key']][0] # user id

        new_top_scores = {
          new_keys[record['key']][0] : i + 2 # user id : place
          for i, record in enumerate(records[1:])
          if record['key'] in new_keys
        }

        # update top leaderboards cache for that level
        self.app.tops[level] = [
          (record['user_id'], record['name'], record['time_taken'], record['timestamp'])
          for record in records
        ]

    embed = discohook.Embed(
      'Times up! Maze Results:',
      description = '\n'.join([
        '{}. <@{}> - {}'.format(
          i + 1, 
          user_id, 
          '`{}s`{}'.format(
            time_taken / 100,
            ' (NEW WORLD RECORD!!!)' if user_id == new_wr_score
            else ' (New Top {}!!)'.format(new_top_scores[user_id]) if user_id in new_top_scores
            else ' (New PB!)' if user_id in new_pb_scores
            else ''
          ) if time_taken else 'FAILED!'
        )
        for i, (user_id, time_taken) in enumerate(scores.items())
      ]),
      color = COLOR_GREEN
    )

    interaction = discohook.Interaction(self.app, {'application_id' : self.app.application_id, 'token' : token}) # partial interaction
    await interaction.response.followup(embed = embed)

    if new_wr_score:
      text = '<@{}> (`{}`) achieved a new world record for Level {}: `{}s`!'.format(
        new_wr_score, names[new_wr_score], level, scores[new_wr_score] / 100
      )
      await self.app.wr_log_webhook.send(text)

  async def check_maze_finished(self, maze_id): # checks if maze that maze timed out or all players finished
    record = await self.get_maze(maze_id)
    if record: # exists
      if time.time() > record['timeout'] or \
      all(
        bool(record[key]) or record[key] == 0 # won or gave up
        for key in record
        if key.isdigit() # user id
      ):
        await self.end_maze(record)

  async def end_timed_out_mazes(self): # used for scheduled actions, has at most a 1 min delay
    query = Query()
    query.less_than('timeout', int(time.time()))
    records = (await self.mazes.fetch([query]))['items']
    for record in records:
      await self.end_maze(record)
  
  async def get_stats(self, user_id):
    query = Query()
    query.equals('user_id', user_id)
    records = (await self.stats.fetch([query], limit = MAX_LEVELS))['items']
    return {
      record['level'] : (record['time_taken'], record['timestamp'])
      for record in records
    }
  
  async def get_top(self, level):
    query = Query()
    query.equals('level', level)
    records = (await self.stats.fetch([query], limit = 10))['items']
    return [
      (record['user_id'], record['name'], record['time_taken'], record['timestamp'])
      for record in records
    ]
