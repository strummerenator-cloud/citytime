# CityTime

A world clock tool with a CLI and a web UI. Look up the current time in any city or timezone, manage custom aliases, and pin cities you care about.

## Features

- Built-in database of hundreds of US and international cities
- Fuzzy matching — type `chicago` or `tokyo` and it just works
- Custom aliases saved to `~/.citytime_aliases`
- Web UI with pinned city clocks, alias management, steampunk clock, and live news headlines
- CLI for scripting and terminal use

## Requirements

- Python 3.9+
- Flask (`pip install flask`) — web UI only

## CLI Usage

```bash
# Get the current time for a city
python3 citytime.py --time chicago
python3 citytime.py --time Tokyo
python3 citytime.py --time "America/New_York"

# Add a custom alias
python3 citytime.py --add hometown America/Chicago

# List all aliases
python3 citytime.py --list

# Batch add aliases from a file (one "city timezone" per line)
python3 citytime.py --batch-add aliases.txt

# Update aliases from the system timezone database
python3 citytime.py --update-aliases

# Interactive menu
python3 citytime.py --interactive
```

## Web UI

```bash
python3 citytime_web.py
```

Then open [http://localhost:5000](http://localhost:5000).

- **Search** any city or timezone and pin it to the dashboard
- **Pinned cities** update live every second
- **Aliases** can be added, pinned, or deleted from the UI
- **Headlines** panel shows top Google News stories, refreshed every 10 minutes

Set a custom port with the `PORT` environment variable:

```bash
PORT=8080 python3 citytime_web.py
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/time/<city>` | Get current time for a city |
| GET | `/api/aliases` | List all aliases |
| POST | `/api/aliases` | Add an alias `{"city": "...", "timezone": "..."}` |
| DELETE | `/api/aliases/<city>` | Remove an alias |
| GET | `/api/search/<query>` | Search cities and timezones |
| GET | `/api/timezones` | List all IANA timezone strings |
| GET | `/api/headlines` | Top news headlines (cached 10 min) |
