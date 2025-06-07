import json
from jinja2 import Environment, FileSystemLoader

# Load the events produced by parse_retreat_events.py --output events.json
with open("events.json", "r", encoding="utf-8") as f:
    retreat_data = json.load(f)
    centers = sorted({r.get('location', {}).get('practice_center', '') for r in retreat_data if r.get('location', {}).get('practice_center')})

env = Environment(loader=FileSystemLoader("."))
template = env.get_template("template.html")

# Render the HTML and save to a file
html_output = template.render(retreats=retreat_data, centers=centers)
with open("retreats.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print("Wrote retreats.html")
