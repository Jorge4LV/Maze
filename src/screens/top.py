import discohook
from ..utils.constants import MAX_LEVELS, COLOR_BLURPLE

async def is_author(interaction):
  if not interaction.from_originator:
    await interaction.response.send('This is not your interaction!', ephemeral = True)
    return False
  return True

def parse_values(interaction):
  return tuple(map(int, interaction.payload['message']['components'][0]['components'][0]['custom_id'].split(':')[2:]))

@discohook.select.text([
  discohook.SelectOption('Level {}'.format(i), str(i)) 
  for i in range(1, MAX_LEVELS + 1)
], placeholder = 'Select a level.', custom_id = 'top_select:v0.0')
async def level_select(interaction, selected):
  level = int(selected[0])
  _level, toggle = parse_values(interaction)
  await TopView(interaction, level, toggle).update()
level_select.checks.append(is_author)

@discohook.button.new('Toggle User Mentions/Usernames', emoji = '📝', custom_id = 'top_toggle:v0.0')
async def toggle_button(interaction):
  level, toggle = parse_values(interaction)
  toggle = int(not toggle)
  await TopView(interaction, level, toggle).update()
toggle_button.checks.append(is_author)

@discohook.button.new('Stop', emoji = '🗑️', custom_id = 'top_stop:v0.0', style = discohook.ButtonStyle.red)
async def stop_button(interaction):
  await interaction.response.update_message(view = None)
stop_button.checks.append(is_author)

class TopView(discohook.View):
  def __init__(self, interaction = None, level = None, toggle = 0):
    super().__init__()

    if interaction:
      self.interaction = interaction
      self.level = level
      self.toggle = toggle

      dynamic_level_select = discohook.Select(
        discohook.SelectType.text,
        placeholder = level_select.placeholder,
        custom_id = '{}:{}:{}'.format(level_select.custom_id, level, toggle)
      )

      options = [
        discohook.SelectOption(option.label, option.value, default = True)
        if str(level) == option.value # shows the current level option as selected
        else option
        for option in level_select.options
      ]

      dynamic_level_select.options = options
      
    else: # persistent
      dynamic_level_select = level_select
    
    self.add_select(dynamic_level_select)
    self.add_buttons(toggle_button, stop_button)

  async def setup(self): # ainit, creates self.embed
    app = self.interaction.client
    level = self.level
    toggle = self.toggle

    data = app.tops.get(level)
    if not data:
      data = await app.db.get_top(level)
      app.tops[level] = data

    self.embed = discohook.Embed(
      'Level {} Leaderboards'.format(level),
      description = '\n'.join(
        '{}. {} - `{}s` (<t:{}:R>)'.format(
          i + 1, 
          name if toggle else '<@{}>'.format(user_id), 
          time_taken / 100, 
          timestamp
        )
        for i, (user_id, name, time_taken, timestamp) in enumerate(data)
      ) if data else 'No data is available yet.',
      color = COLOR_BLURPLE
    )

  async def send(self):
    await self.setup()
    await self.interaction.response.send(embed = self.embed, view = self)

  async def update(self):
    await self.setup()
    await self.interaction.response.update_message(embed = self.embed, view = self)