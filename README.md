# Disstat

Disstat is a Python package for computing dissimilarity statistics for wrapping the Disstat API.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install disstat.

```bash
pip install disstat
```

## Usage

```python
from discord import Intents, Interaction
from discord.ext import commands
from disstat import DisstatClient


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=Intents.default())
        self.disstat = DisstatClient(self, "DISSTAT API KEY HERE")

    async def on_ready(self):
        await self.disstat.start_auto_post()

    async def on_command_completion(
        self, ctx: commands.Context
    ):  # For using prefix commands
        await self.disstat.post_command(
            ctx.command.name,
            invoker_id=ctx.user.id,
            guild_id=(ctx.guild.id if ctx.guild else None),
        )

    async def on_app_command_completion(
        self, interaction: Interaction
    ):  # For using slash commands
        await self.disstat.post_command(
            interaction.command.name,
            invoker_id=interaction.user.id,
            guild_id=(interaction.guild.id if interaction.guild else None),
        )

    async def on_disstat_post(self, payload):
        print("Posted stats to Disstat.")

    async def on_disstat_post_command(self, payload):
        print(f"Posted command {payload['command']} to Disstat.")


bot = Bot()

bot.run("TOKEN")
```
