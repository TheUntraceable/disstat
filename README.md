# Disstat

Disstat is a Python package for computing dissimilarity statistics for wrapping the Disstat API.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install disstat.

```bash
pip install disstat
```

## Usage

```python
from disstat import DisstatClient
from discord.ext import commands

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.disstat = DisstatClient(self, "DISSTAT API KEY HERE")

    async def on_ready(self):
        await self.disstat.start_auto_post()

    async def on_command_completion(self, ctx):  # For using prefix commands
        await self.disstat.post_command(ctx.command.name, ctx.user.id, (ctx.guild.id if ctx.guild else None))

    async def on_app_command_completion(self, interaction):  # For using slash commands
        await self.disstat.post_command(interaction.command.name, interaction.user.id, (interaction.guild.id if interaction.guild else None))

    async def on_disstat_post(self, payload):
        print("Posted stats to Disstat.")

    async def on_disstat_post_command(self, payload):
        print(f"Posted command {payload['command']} to Disstat.")

bot = Bot()

bot.run("TOKEN")

```
