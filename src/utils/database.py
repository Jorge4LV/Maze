from deta import Deta

class Database(Deta):
  def __init__(self, app, key):
    super().__init__(key)
    self.app = app