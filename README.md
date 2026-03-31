# pyfc ⚽

A command-line tool that displays today's football (soccer) matches right in your terminal. Powered by the [football-data.org](https://www.football-data.org/) API.

## Requirements

- Python 3.10+
- A free API key from [football-data.org](https://www.football-data.org/client/register)

## Installation

```bash
pip install .
```

Or install in development mode:

```bash
pip install -e .
```

## Usage

```bash
pyfc
```

On first run, you'll be prompted to enter your football-data.org API key. The key is saved to `~/.config/pyfc/credentials.env` (or `$XDG_CONFIG_HOME/pyfc/credentials.env`) so you only need to enter it once.

## Running Tests

```bash
pip install pytest
pytest
```

