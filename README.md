# ⚽ CPL SDK

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A modern Python SDK for the CPL (Canadian Premier League) API using httpx.

## Features

- Type-annotated responses for IDE support
- Team standings, schedules, and statistics
- Error handling and logging

## Installation

```bash
pip install git+https://@github.com/ojadeyemi/cpl-sdk.git
```

## Quick Start

```python
from cpl import CPLClient

# Create client
client = CPLClient()

# Get standings
teams = client.standing()

# Get player career details
player_career = sdk.get_player_career("PLAYER_ID")

# Close the connection when done
sdk.close()
```
