# Retreat Guide

This repository provides a script that parses sesshin events from the San Francisco Zen Center calendar.

## Requirements

- Python 3.8+
- `requests`
- `beautifulsoup4`

Install dependencies using:

```bash
pip install -r requirements.txt
```

## Usage

Run the parser:

```bash
python parse_sesshin_events.py
```

The script prints the date, info and link for each calendar event that includes the word "sesshin" in its title.
