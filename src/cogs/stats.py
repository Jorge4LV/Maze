import discohook
from ..utils.constants import COLOR_BLURPLE

@discohook.command.slash('stats', description = 'View your stats or someone else\'s!', options = [
  discohook.Option.user('user', 'View this user\'s stats.')
])
async def stats_command(interaction, user = None):
  if not user:
    user = interaction.author
  
  user_id = int(user.id)
  app = interaction.client

  # get data from cache or fetch from db
  data = app.stats.get(user_id)
  if not data:
    data = await app.db.get_stats(user.id) # user id fetch is string
    app.stats[user_id] = data
  
  # data looks like [(1, 1230, 1600000), ...] / (level, 0.01s timetaken, timestamp)
  embed = discohook.Embed(
    '{}\'s Stats'.format(user),
    description = '\n'.join(
      'Level {}: `{}s` - <t:{}:R>'.format(level, time_taken / 100, timestamp)
      for level, (time_taken, timestamp) in data.items()
    ) if data else 'No data is available yet.',
    color = COLOR_BLURPLE
  )
  embed.set_thumbnail(user.avatar.url)

  await interaction.response.send(embed = embed)