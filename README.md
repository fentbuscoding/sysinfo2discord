# System Monitor Discord Rich Presence

A modern Python script to monitor and display CPU, memory, disk I/O, and network I/O via Discord Rich Presence.

## Features

- Shows live system stats (CPU, RAM, Disk, Network) in your Discord status
- Rotates between different stat combinations for a dynamic presence
- Human-readable formatting for all sizes (e.g., MB, GB)
- Simple, no-logging, no-file-output, just Discord RPC

## Requirements

- Python 3.7+
- [psutil](https://pypi.org/project/psutil/)
- [pypresence](https://pypi.org/project/pypresence/)

## Installation

```sh
pip install -r requirements.txt
```

## Usage

```sh
python discord.py
```

### Optional arguments

- `--rpc-update-interval`: How often to update Discord status (seconds, default: 10)
- `--discord-client-id`: Your Discord Application Client ID (default: provided in script)

Example:

```sh
python discord.py --rpc-update-interval 5 --discord-client-id 123456789012345678
```

## Notes

- You must have Discord running on your computer for Rich Presence to work.
- If you want your own icon/images, set them up in your Discord Developer Portal and use your own Client ID.

## License

MIT License