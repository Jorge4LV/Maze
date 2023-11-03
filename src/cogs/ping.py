import time
import discohook

@discohook.command.slash('ping', description = 'Ping test the bot!')
async def ping_command(interaction):
  created_at = interaction.created_at
  now = time.time()
  since = now - created_at
  content = 'Pong! Latency: `{:.2f}ms`'.format(since * 1000)
  await interaction.response.send(content)

  """ debugging issue with lib
  url = '.'.join(str(interaction.author.avatar).split('.')[:-1]) + '.png?size=512'
  async with interaction.client.session.get(url) as resp:
    if resp.status != 200:
      raise ValueError('Fetch avatar returned bad status', resp.status)
    avatar_file = discohook.File('avatar.png', content = await resp.read())
  
  embed = discohook.Embed('title')
  embed.set_image(avatar_file)

  await interaction.response.send('content', embed = embed, file = avatar)"""