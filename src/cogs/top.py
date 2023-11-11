import discohook
from ..utils.constants import MAX_LEVELS

@discohook.command.slash('top', description = 'View the global leaderboards!', options = [
  discohook.Option.integer('level', 'Select the level difficulty.', choices = [
    discohook.Choice(name = 'Level {0}'.format(i), value = i)
    for i in range(1, MAX_LEVELS + 1)
  ])
])
async def top_command(interaction, level = None):
  await interaction.response.send('top {}'.format(level))