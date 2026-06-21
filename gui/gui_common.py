#!/usr/bin/python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import os, subprocess, threading, re

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR1     = os.path.join(BASE, 'part1')
DIR2     = os.path.join(BASE, 'part2')
DIR3     = os.path.join(BASE, 'part3')
DIR4     = os.path.join(BASE, 'part4')

FILE_SH  = os.path.join(DIR1, 'filemanagement.sh')
TASK_SH  = os.path.join(DIR1, 'taskmanagement.sh')
TIME_SH  = os.path.join(DIR1, 'timemanagement.sh')
INST_SH  = os.path.join(DIR1, 'installanduninstall.sh')
PROC_BIN = os.path.join(DIR2, 'process')
PROC_SRC = os.path.join(DIR2, 'process.c')
NET_BIN  = os.path.join(DIR2, 'network')
NET_SRC  = os.path.join(DIR2, 'network.c')
FMGMT_BIN= os.path.join(DIR2, 'filemanagement')
FMGMT_SRC= os.path.join(DIR2, 'filemanagement.c')

CSS = b"""
.title-bar {
    background-color: #085696;
    color: white;
    font-weight: bold;
    font-size: 15px;
    padding: 7px 4px;
    min-height: 32px;
}
.section-lbl {
    color: #888888;
    font-size: 11px;
    font-weight: bold;
    padding: 6px 12px 2px 12px;
}
.nav-btn {
    background: white;
    background-image: none;
    color: #222222;
    font-weight: bold;
    font-size: 13px;
    border: none;
    border-radius: 0;
    box-shadow: none;
    min-height: 34px;
    padding: 0 10px;
}
.nav-btn:hover { background-color: #d4e8f8; background-image: none; }
.nav-btn.active,
.nav-btn.active:hover {
    background-color: #085696;
    background-image: none;
    color: white;
}
button.act {
    background: #085696;
    background-image: none;
    color: white;
    font-weight: bold;
    border-radius: 8px;
    padding: 5px 14px;
    min-height: 32px;
    min-width: 80px;
    border: none;
    box-shadow: none;
}
button.act:hover { background: #0a6bbf; background-image: none; }
button.act:disabled { background: #8aaecc; background-image: none; color: #ddd; }
button.act.danger { background: #b52020; }
button.act.danger:hover { background: #d42828; }
.term {
    background-color: #1e1e1e;
    color: #00cc44;
    font-family: monospace;
    font-size: 12px;
    padding: 6px;
}
.kern-lbl {
    font-size: 14px;
    font-weight: bold;
}
.kern-combo {
    font-size: 14px;
    min-height: 36px;
}
.kern-spin {
    font-size: 14px;
    min-width: 64px;
    min-height: 36px;
}
.kern-cell {
    font-size: 15px;
    min-width: 52px;
    min-height: 36px;
}
.kern-frame-lbl {
    font-size: 13px;
    font-weight: bold;
}
"""

# ── Chạy lệnh ────────────────────────────────────────────────────────────────

def run_cmd(cmd, cwd=None, inp=None):
    r = subprocess.run(cmd, shell=True, capture_output=True,
                       text=True, cwd=cwd, input=inp)
    return r.stdout, r.stderr, r.returncode

def run_bg(cmd, cwd=None, inp=None, callback=None):
    def _w():
        o, e, rc = run_cmd(cmd, cwd=cwd, inp=inp)
        if callback:
            GLib.idle_add(callback, o, e, rc)
    threading.Thread(target=_w, daemon=True).start()

def pipe_sh(script, choices, cwd=None):
    inp = '\n'.join(str(c) for c in choices) + '\n'
    return run_cmd(f'bash "{script}"', cwd=cwd, inp=inp)

def pipe_sh_bg(script, choices, cwd=None, callback=None):
    inp = '\n'.join(str(c) for c in choices) + '\n'
    run_bg(f'bash "{script}"', cwd=cwd, inp=inp, callback=callback)

def pipe_bin(binary, choices, cwd=None, sudo=False):
    inp = '\n'.join(str(c) for c in choices) + '\n'
    prefix = 'sudo ' if sudo else ''
    return run_cmd(f'{prefix}"{binary}"', cwd=cwd, inp=inp)

def pipe_bin_bg(binary, choices, cwd=None, sudo=False, callback=None):
    inp = '\n'.join(str(c) for c in choices) + '\n'
    prefix = 'sudo ' if sudo else ''
    run_bg(f'{prefix}"{binary}"', cwd=cwd, inp=inp, callback=callback)

def ensure_compiled(src, out):
    if os.path.exists(out):
        return True, ''
    o, e, rc = run_cmd(f'gcc -o "{out}" "{src}"')
    if rc != 0:
        return False, f'Biên dịch thất bại:\n{e}'
    return True, f'Đã biên dịch: {os.path.basename(out)}\n'

def open_terminal(cmd):
    wrap = cmd + '; read -p "Nhấn Enter để đóng'
    '"'
    for term, args in [
        ('ptyxis',         lambda: ['ptyxis', '--', 'bash', '-c', wrap]),
        ('gnome-terminal', lambda: ['gnome-terminal', '--', 'bash', '-c', wrap]),
        ('xfce4-terminal', lambda: ['xfce4-terminal', '--', 'bash', '-c', wrap]),
        ('konsole',        lambda: ['konsole', '-e', 'bash', '-c', wrap]),
        ('xterm',          lambda: ['xterm', '-fa', 'Monospace', '-fs', '11',
                                    '-e', 'bash', '-c', wrap]),
    ]:
        if run_cmd(f'which {term}')[2] == 0:
            subprocess.Popen(args())
            return
    subprocess.Popen(['bash', '-c', cmd])

# ── Widget helpers ────────────────────────────────────────────────────────────

def _dlg(parent, mtype, buttons, title, body=''):
    d = Gtk.MessageDialog(transient_for=parent, modal=True,
                          message_type=mtype, buttons=buttons, text=title)
    if body:
        d.format_secondary_text(body)
    r = d.run(); d.destroy(); return r

def info(p, t, b=''): _dlg(p, Gtk.MessageType.INFO,    Gtk.ButtonsType.OK, t, b)
def err(p,  t, b=''): _dlg(p, Gtk.MessageType.ERROR,   Gtk.ButtonsType.OK, t, b)
def warn(p, t, b=''): _dlg(p, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK, t, b)
def ask(p,  t, b=''):
    return _dlg(p, Gtk.MessageType.QUESTION,
                Gtk.ButtonsType.YES_NO, t, b) == Gtk.ResponseType.YES

def title_lbl(text):
    l = Gtk.Label(label=text)
    l.get_style_context().add_class('title-bar')
    l.set_hexpand(True); l.set_xalign(0.5)
    return l

def act_btn(label, danger=False):
    b = Gtk.Button(label=label)
    b.set_can_focus(False)
    b.get_style_context().add_class('act')
    if danger:
        b.get_style_context().add_class('danger')
    return b

def make_term():
    tv = Gtk.TextView()
    tv.set_editable(False)
    tv.set_wrap_mode(Gtk.WrapMode.CHAR)
    tv.get_style_context().add_class('term')
    sw = Gtk.ScrolledWindow()
    sw.set_hexpand(True); sw.set_vexpand(True)
    sw.set_min_content_height(160); sw.add(tv)
    return tv, sw

def entry(placeholder=''):
    e = Gtk.Entry()
    if placeholder:
        e.set_placeholder_text(placeholder)
    e.set_hexpand(True)
    return e

def tv_text(tv):
    b = tv.get_buffer()
    return b.get_text(b.get_start_iter(), b.get_end_iter(), True)

# ── ANSI parser ───────────────────────────────────────────────────────────────

_ANSI_RE = re.compile(r'\033\[([0-9;]*)m')
_ANSI_FG = {
    '30': '#555555', '31': '#ff5555', '32': '#55ff55',
    '33': '#ffff55', '34': '#8888ff', '35': '#ff55ff',
    '36': '#55ffff', '37': '#ffffff',
    '90': '#888888', '91': '#ff6666', '92': '#66ff66',
    '93': '#ffff66', '94': '#aaaaff', '95': '#ff88ff',
    '96': '#88ffff', '97': '#ffffff',
}

def term_write(tv, text):
    buf = tv.get_buffer()
    fg = None
    bold = False
    last = 0
    for m in _ANSI_RE.finditer(text):
        if m.start() > last:
            _buf_insert(buf, text[last:m.start()], fg, bold)
        codes = m.group(1).split(';') if m.group(1) else ['0']
        for c in codes:
            if c in ('0', ''):
                fg = None; bold = False
            elif c == '1':
                bold = True
            elif c in _ANSI_FG:
                fg = _ANSI_FG[c]
        last = m.end()
    if last < len(text):
        _buf_insert(buf, text[last:], fg, bold)
    tv.scroll_to_iter(buf.get_end_iter(), 0.0, False, 0, 0)

def _buf_insert(buf, text, fg, bold):
    if not text:
        return
    if fg or bold:
        tag_name = f'c_{fg}_{bold}'
        tag = buf.get_tag_table().lookup(tag_name)
        if tag is None:
            kwargs = {}
            if fg:
                kwargs['foreground'] = fg
            if bold:
                kwargs['weight'] = 700
            tag = buf.create_tag(tag_name, **kwargs)
        buf.insert_with_tags(buf.get_end_iter(), text, tag)
    else:
        buf.insert(buf.get_end_iter(), text)

def term_clear(tv):
    tv.get_buffer().set_text('')
