import discohook

@discohook.command.slash('maze', description = 'Starts a maze race!')
async def maze_command(interaction):
  await interaction.response.send('maze')