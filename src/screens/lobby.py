import discohook
from .constants import COLOR_GREEN, COLOR_ORANGE, COLOR_RED

@discohook.button.new('Start', emoji = '🏁', style = discohook.ButtonStyle.green, custom_id = 'start:v0.0')
async def start_button(interaction):
  await interaction.response.send('click Start')

@discohook.button.new('Join', emoji = '🚪', custom_id = 'join:v0.0')
async def join_button(interaction):
  await interaction.response.send('click Join')

@discohook.button.new('Cancel', emoji = '🏳️', style = discohook.ButtonStyle.red, custom_id = 'cancel:v0.0')
async def cancel_button(interaction):
  embed = interaction.message.embeds[0]
  embed.color = COLOR_RED
  embed.set_footer('Game was cancelled by the host.')
  await interaction.response.update_message(embed = embed, view = None)

class LobbyView(discohook.View):
  def __init__(self, interaction = None, flag = None, data = None):
    super().__init__()
    if interaction:
      self.interaction = interaction

      if not flag: # lobby

        self.embed = discohook.Embed(
          'Maze Lobby',
          description = '\n'.join([
            'A new maze race is being hosted by <@{}>.'.format(interaction.author.id),
            'Everyone else click **Join** to join!',
            'When everyone is ready, tell the host to press **Start** to start. (60s)'
          ]),
          color = COLOR_GREEN
        )

        self.embed.add_field(
          'Details',
          '\n'.join([
            'Level: `1`',
            'Size: `7x7`',
            'Time: `60s`'
          ])
        )
        
        if data:
          players = data
        else:
          players = [interaction.author.id]

        self.embed.add_field(
          'Players ({})'.format(len(players)),
          '<@{}>'.format('> <@'.join(i for i in players))
        )

        self.add_buttons(start_button, join_button, cancel_button)

      elif flag == 1: # started
        pass
      elif flag == 2: # finished
        pass
      else:
        raise ValueError('Unhandled LobbyView flag', flag)

    else: # persistent view
      self.add_buttons(start_button, join_button, cancel_button)
  
  async def send(self):
    await self.interaction.response.send(embed = self.embed, view = self)

  async def update(self):
    await self.interaction.response.update_message(embed = self.embed, view = self)