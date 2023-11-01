import discohook
from ..utils.constants import COLOR_GREEN, COLOR_ORANGE, COLOR_RED, MAX_PLAYERS

async def is_host(interaction):
  if not interaction.from_originator:
    await interaction.response.send('Denied because you are not the host!', ephemeral = True)
    return False
  return True

@discohook.button.new('Start', emoji = '🏁', style = discohook.ButtonStyle.green, custom_id = 'start:v0.0')
async def start_button(interaction):
  await interaction.response.send('click Start')
start_button.checks.append(is_host)

@discohook.button.new('Join', emoji = '🚪', custom_id = 'join:v0.0')
async def join_button(interaction):
  embed = interaction.message.embeds[0]
  text = embed.fields[1]['value']

  if interaction.author.id in text: # text is players embed field value
    return await interaction.response.send('You are already in the game.', ephemeral = True)
  elif len(text.split('\n')) == MAX_PLAYERS: # player count
    return await interaction.response.send('Can\'t join, maximum players reached ({}).'.format(MAX_PLAYERS))

  text += '\n' + interaction.author.mention # add their mention to text

  embed.fields.pop() # update the players field
  embed.add_field(
    'Players ({})'.format(len(text.split(' '))),
    text,
    inline = True
  )

  await LobbyView(interaction, 1, data = embed).update()

@discohook.button.new('Cancel', emoji = '🏳️', style = discohook.ButtonStyle.red, custom_id = 'cancel:v0.0')
async def cancel_button(interaction):
  embed = interaction.message.embeds[0]
  embed.color = COLOR_RED
  embed.set_footer('Game was cancelled by the host.')
  await interaction.response.update_message(embed = embed, view = None)
cancel_button.checks.append(is_host)

class LobbyView(discohook.View):
  def __init__(self, interaction = None, flag = None, data = None):
    super().__init__()

    if interaction:
      self.interaction = interaction

      if not flag: # start (used /maze)

        self.embed = discohook.Embed(
          'Maze Lobby',
          description = '\n'.join([
            'A new maze race is being hosted by <@{}>.'.format(interaction.author.id),
            'Everyone else click **Join** to join!',
            'When everyone is ready, tell the host to press **Start** to start.'
          ]),
          color = COLOR_GREEN
        )
        
        level = data
        helpers = interaction.client.helpers
        size = helpers.level_to_size(level)
        seconds = helpers.level_to_seconds(level)

        self.embed.add_field(
          'Details',
          '\n'.join([
            'Level: `{}`'.format(level),
            'Size: `{0}x{0}`'.format(size),
            'Time: `{}s`'.format(seconds)
          ]),
          inline = True
        )

        self.embed.add_field('Players (1)', interaction.author.mention, inline = True)

        self.add_buttons(start_button, join_button, cancel_button)

      elif flag == 1: # update lobby (someone successfully clicked Join)

        self.embed = data

        self.add_buttons(start_button, join_button, cancel_button)
          
      elif flag == 2: # started (host clicked Start)
        pass
      elif flag == 3: # finished (everyone finished playing/timed out)
        pass
      else:
        raise ValueError('Unhandled LobbyView flag', flag)

    else: # persistent view
      self.add_buttons(start_button, join_button, cancel_button)
  
  async def send(self):
    await self.interaction.response.send(embed = self.embed, view = self)

  async def update(self):
    await self.interaction.response.update_message(embed = self.embed, view = self)