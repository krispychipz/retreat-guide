# Retreat Guide

This repository provides a script that gathers retreat events from the San Francisco Zen Center website.

## Requirements

- Python 3.8+
- `requests`
- `beautifulsoup4`

Install dependencies using:

```bash
pip install -r requirements.txt
```

## Usage

Run the script:

```bash
python parse_sesshin_events.py
```

Add `--debug` to see detailed parsing information:

```bash
python parse_sesshin_events.py --debug
```

The script prints dates, info, links, and the source URL for events whose title includes one of the keywords `retreat`, `sesshin`, or `One-Day Sitting`.
