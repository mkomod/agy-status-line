# Status Line Plugin for Antigravity CLI

A compact, configurable status line for the Antigravity CLI showing your usage
quotas and context-window fill as colour-coded bars.

The Antigravity CLI pipes a JSON status payload to the status-line command on
**stdin** for every render. This plugin reads that payload — it does not scrape
local files.

## Features

- **Usage Limits** — 5-hour and weekly quota bars (filling as you use them) with reset countdowns, for the active model group
- **Context Window** — Bar showing how full the context window is
- **Clock** — Optional current-time segment
- **Configurable** — Toggle segments, pick colours, and tune the bar style via `config.toml`
- **Responsive** — Wraps onto multiple lines when the terminal is too narrow

Example (wide terminal):

```
5h: █░░░░░░░ 14% reset 3h 37m  |  7d: ░░░░░░░░ 2% reset 6d 22h  |  ctx: █░░░░░░░ 8%
```

## Installation

```bash
bash install.sh
```

This points your Antigravity CLI status line at `status_line.py`.

## Configuration

All configuration lives in `config.toml` next to the script:

```toml
[modules]            # toggle segments on/off; this order is the render order
"5h" = true          # 5-hour usage quota
"7d" = true          # weekly usage quota
ctx = true           # context-window fill
clock = false        # current time

[colors]             # named: black, red, green, yellow, blue, magenta,
bar = "green"        #        cyan, white, gray, dim, none
value = "green"      # percentages and clock time
label = "dim"        # labels, empty bar portion, reset countdowns

[display]
bar_width = 8        # characters per bar
separator = "  |  "  # text between segments
fill_char = "█"      # filled bar character
empty_char = "░"     # empty bar character
fallback_width = 80  # assumed terminal width when the payload omits it

[color_codes]        # colour name -> ANSI escape (use the  ESC escape)
green = "[92m"
dim   = "[2m"
reset = "[0m"  # "reset" is required
# ... red, yellow, blue, magenta, cyan, white, gray, black, none
```

Every presentational value lives here — segments, colour roles, the ANSI codes
themselves, and bar style. If `config.toml` is missing or a value is omitted,
safe built-in fallbacks are used (uncoloured but functional).

## Project Structure

```
.
├── status_line.py   # The status line (reads stdin payload, renders bars)
├── config.toml      # Segment / colour / display configuration
├── install.sh       # Installation script
└── plugin.json      # Plugin metadata
```

## Notes

- The quota group shown follows the active model: `gemini-*` quotas for Gemini models, `3p-*` for Claude/GPT models.
- **Install mechanisms:** `plugin.json` declares a `hooks.statusLine` entry, while `install.sh` writes a `statusLine.command` block (with an absolute path) into `~/.gemini/antigravity-cli/settings.json`. `install.sh` is the one users run.
