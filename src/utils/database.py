import time
from deta import Deta, Query, Record, Updater

class Database(Deta):
  def __init__(self, app, key):
    super().__init__(key)
    self.app = app


  async def create_maze(self, maze_id, grid, start, end, timeout, token, player_ids):

    data = {
      'grid' : grid,
      'start' : start,
      'end' : end,
      'timeout' : timeout,
      'token' : token # to do Maze results followup
    }

    for user_id in player_ids:
      data[user_id] = None # None = DQed, otherwise time taken

    print('save this record', data, maze_id)
    #record = Record(data, key = maze_id)

    #await self.app.insert(record)
    

  async def get_maze(self, maze_id): # function reloaded
    query = Query()

    pass

  async def update_maze(self, player_id, seconds): # someone won
    pass
    
  async def end_maze(self, maze_id):
    pass