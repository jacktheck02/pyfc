# pyfc

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

By default, `pyfc` displays matches for today.

You can also query matches across a date range using `--date-from` and `--date-to`:

```bash
pyfc --date-from 2026-04-01 --date-to 2026-04-07
```

Both flags accept dates in `YYYY-MM-DD` format. `--date-to` is inclusive. If only `--date-from` is provided, it defaults to showing matches from that date to today. If neither flag is specified, only today's matches are shown.

On first run, you'll be prompted to enter your football-data.org API key. The key is saved to `~/.config/pyfc/credentials.env` (or `$XDG_CONFIG_HOME/pyfc/credentials.env`) so you only need to enter it once.

## Running Tests

```bash
pip install pytest
pytest
```

