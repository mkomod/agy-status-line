#!/usr/bin/env python3
"""Status line generator for the Gemini Antigravity CLI.

Reads the JSON status payload piped in on stdin by the Antigravity CLI and
renders a compact line of usage bars. Everything presentational — which segments
show, their colours, the ANSI colour codes themselves, bar width/characters, and
the separator — lives in ``config.toml``. Bars fill up as a resource is consumed.
"""
import os
import re
import json
import sys
import datetime
import tomllib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ANSI_RE = re.compile(r'\033\[[0-9;]*m')


def read_payload():
    """Read and parse the JSON status payload piped in on stdin."""
    try:
        if sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def load_config():
    """Return (modules map, style dict) from config.toml, with safe fallbacks."""
    try:
        with open(os.path.join(SCRIPT_DIR, 'config.toml'), 'rb') as f:
            cfg = tomllib.load(f)
    except Exception:
        cfg = {}

    modules = cfg.get('modules') or {'5h': True, '7d': True, 'ctx': True, 'clock': False}
    codes = cfg.get('color_codes') or {}
    roles = cfg.get('colors') or {}
    display = cfg.get('display') or {}

    # Roles always resolve to a (possibly empty) code, so segments never KeyError.
    colors = {'bar': '', 'value': '', 'label': ''}
    colors.update({role: codes.get(name, '') for role, name in roles.items()})

    style = {
        'colors': colors,
        'reset': codes.get('reset', ''),
        'bar_width': display.get('bar_width', 8),
        'separator': display.get('separator', '  |  '),
        'fill_char': display.get('fill_char', '█'),
        'empty_char': display.get('empty_char', '░'),
        'fallback_width': display.get('fallback_width', 80),
    }
    return modules, style


def _bar(frac, style):
    """A progress bar that fills from empty to full as frac goes 0 -> 1."""
    frac = min(max(frac, 0.0), 1.0)
    width = style['bar_width']
    filled = int(round(frac * width))
    colors, reset = style['colors'], style['reset']
    return (f"{colors['bar']}{style['fill_char'] * filled}{reset}"
            f"{colors['label']}{style['empty_char'] * (width - filled)}{reset}")


def _fmt_reset(seconds):
    """Format a reset countdown like '4h 3m' or '1d 21h'."""
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days > 0:
        return f"{days}d {hours}h"
    return f"{hours}h {minutes}m"


def _quota_segment(payload, style, label, window):
    """Render a quota bar (filling with usage) for the active model group."""
    quota = payload.get('quota') or {}
    model_id = ((payload.get('model') or {}).get('id') or '').lower()
    prefix = 'gemini' if 'gemini' in model_id else '3p'
    q = quota.get(f'{prefix}-{window}')
    if not q:
        return None
    colors, reset = style['colors'], style['reset']
    used = 1 - q.get('remaining_fraction', 0)
    reset_in = _fmt_reset(q.get('reset_in_seconds', 0))
    return (f"{colors['label']}{label}:{reset} {_bar(used, style)} "
            f"{colors['value']}{used * 100:.0f}%{reset} "
            f"{colors['label']}reset {reset_in}{reset}")


def seg_5h(payload, style):
    return _quota_segment(payload, style, '5h', '5h')


def seg_7d(payload, style):
    return _quota_segment(payload, style, '7d', 'weekly')


def seg_ctx(payload, style):
    cw = payload.get('context_window')
    if not cw:
        return None
    colors, reset = style['colors'], style['reset']
    used = cw.get('used_percentage', 0) / 100
    return (f"{colors['label']}ctx:{reset} {_bar(used, style)} "
            f"{colors['value']}{used * 100:.0f}%{reset}")


def seg_clock(payload, style):
    colors, reset = style['colors'], style['reset']
    now = datetime.datetime.now().strftime('%H:%M')
    return f"{colors['label']}🕒{reset} {colors['value']}{now}{reset}"


SEGMENTS = {
    '5h': seg_5h,
    '7d': seg_7d,
    'ctx': seg_ctx,
    'clock': seg_clock,
}


def _visible_len(s):
    """Length of a string ignoring ANSI colour codes."""
    return len(ANSI_RE.sub('', s))


def _wrap(parts, width, sep):
    """Join segments with sep, breaking to a new line when width is exceeded."""
    lines = []
    current = ''
    for part in parts:
        if not current:
            current = part
        elif _visible_len(current) + len(sep) + _visible_len(part) <= width:
            current += sep + part
        else:
            lines.append(current)
            current = part
    if current:
        lines.append(current)
    return '\n'.join(lines)


def main():
    """Build and print the status line to stdout."""
    payload = read_payload()
    modules, style = load_config()

    parts = []
    for name, enabled in modules.items():
        if enabled and name in SEGMENTS:
            segment = SEGMENTS[name](payload, style)
            if segment:
                parts.append(segment)

    width = payload.get('terminal_width') or style['fallback_width']
    print(_wrap(parts, width, style['separator']))


if __name__ == '__main__':
    main()
