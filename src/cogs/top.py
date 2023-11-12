import discohook
from ..screens.top import TopView
from ..utils.constants import MAX_LEVELS

@discohook.command.slash('top', description = 'View the global leaderboards!', options = [
  discohook.Option.integer('level', 'Select the level difficulty.', choices = [
    discohook.Choice(name = 'Level {0}'.format(i), value = i)
    for i in range(1, MAX_LEVELS + 1)
  ])
])
async def top_command(interaction, level = 1):
  await TopView(interaction, level).send()