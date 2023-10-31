import discohook
from ..screens.lobby import LobbyView

@discohook.command.slash('maze', description = 'Starts a maze race!')
async def maze_command(interaction):
  await LobbyView(interaction).send()