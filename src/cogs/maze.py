import discohook
from ..screens.lobby import LobbyView
from ..utils.constants import MAX_LEVELS, IMAGE_SIZE
from ..utils.helpers import level_to_size

@discohook.command.slash('maze', description = 'Starts a maze race!', 
  options = [
    discohook.Option.integer('level', 'Select the level difficulty.', required = True, choices = [
      discohook.Choice(name = 'Level {0} ({1}x{1})'.format(i, level_to_size(i)), value = i)
      for i in range(1, MAX_LEVELS + 1)
    ]),
    discohook.Option.integer('image_size', 'Select the image size, smaller = loads faster, default is 1024x1024.', choices = [
      discohook.Choice(name = '{0}x{0}'.format(i), value = i)
      for i in (1024, 512, 256)
    ]),
    discohook.Option.boolean('coop', 'Whether to allow other people to click maze buttons. Default is false.')
  ],
  integration_types = [
    discohook.ApplicationIntegrationType.user,
    discohook.ApplicationIntegrationType.guild
  ],
  contexts = [
    discohook.InteractionContextType.guild,
    discohook.InteractionContextType.bot_dm,
    discohook.InteractionContextType.private_channel
  ]
)
async def maze_command(interaction, level, image_size = IMAGE_SIZE, coop = False):
  if image_size/level_to_size(level) < 8:
    return await interaction.response.send('Image size `{0}x{0}` is too small for level `{1}`. Pick a bigger size.'.format(image_size, level), ephemeral = True)
  await LobbyView(interaction, level, image_size, coop).send()