import discohook
from ..screens.lobby import LobbyView
from ..utils.constants import MAX_LEVELS
from ..utils.helpers import level_to_size

@discohook.command.slash('maze', description = 'Starts a maze race!', options = [
  discohook.Option.integer('level', 'Select the level difficulty.', required = True, choices = [
    discohook.Choice(name = 'Level {0} ({1}x{1})'.format(i, level_to_size(i)), value = i)
    for i in range(1, MAX_LEVELS + 1)
  ])
])
async def maze_command(interaction, level):
  await LobbyView(interaction, level).send()