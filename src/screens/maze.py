import discohook

@discohook.button.new(emoji = '⬅️', custom_id = 'left:v0.0')
async def left_button(interaction):
  await interaction.response.send('clicked left')

@discohook.button.new(emoji = '➡️', custom_id = 'right:v0.0')
async def right_button(interaction):
  await interaction.response.send('clicked right')

@discohook.button.new(emoji = '⬆️', custom_id = 'up:v0.0')
async def up_button(interaction):
  await interaction.response.send('clicked up')

@discohook.button.new(emoji = '⬇️', custom_id = 'down:v0.0')
async def down_button(interaction):
  await interaction.response.send('clicked down')

@discohook.button.new('Give Up', emoji = '🏳️', style = discohook.ButtonStyle.red, custom_id = 'giveup:v0.0')
async def giveup_button(interaction):
  await interaction.response.send('clicked giveup')

class MazeView(discohook.View):
  def __init__(self, interaction = None, flag = None, data = None):
    super().__init__()

    if interaction:
      self.interaction = interaction
      
      if not flag: # race begin
        maze_id, self.content, self.embed, self.image = data

        # use the maze id to add into left position, and start position somehow
        self.add_buttons(left_button, right_button, up_button, down_button, giveup_button)
      
      elif flag == 1: # update position (clicked a button)
        pass
      
      else:
        raise ValueError('Unhandled MazeView flag', flag)

    else: # persistent
      self.add_buttons(left_button, right_button, up_button, down_button, giveup_button)

  async def followup(self): # for race begin only
    await self.interaction.followup(self.content, embed = self.embed, view = self, file = self.image)