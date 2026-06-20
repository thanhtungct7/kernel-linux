#!/usr/bin/python3
"""Part 4 – Keyboard IRQ Driver: kbd_driver.c"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os

from gui.gui_common import (
    DIR4,
    run_bg, run_cmd,
    title_lbl, act_btn, make_term,
    term_write, term_clear,
    warn, ask,
)


class KbdDriverPanel(Gtk.Box):
    DEVICE = '/dev/kbd_log'

    def __init__(self, win):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.win = win
        self.pack_start(title_lbl('Keyboard IRQ Driver  [kbd_driver.c]'), False, False, 0)

        note = Gtk.Label(
            label='IRQ 1 → workqueue → circular buffer → /dev/kbd_log\n'
                  'Cần build rồi sudo insmod kbd_driver.ko trước khi đọc.')
        note.set_margin_start(12); note.set_margin_top(8)
        note.set_halign(Gtk.Align.START)
        self.pack_start(note, False, False, 0)

        row1 = Gtk.Box(spacing=8, margin_start=12, margin_end=12, margin_top=10)
        for lbl, cb, danger in [
            ('Build (make)',             self._build,   False),
            ('Load  (sudo insmod)',      self._load,    False),
            ('Unload  (sudo rmmod)',     self._unload,  True),
        ]:
            b = act_btn(lbl, danger=danger)
            b.connect('clicked', cb)
            row1.pack_start(b, False, False, 0)
        self.pack_start(row1, False, False, 0)

        row2 = Gtk.Box(spacing=8, margin_start=12, margin_end=12, margin_top=6)
        for lbl, cb in [
            ('Đọc /dev/kbd_log', self._read),
            ('Xem dmesg (kbd)', self._dmesg),
            ('Xóa màn hình',    lambda _: term_clear(self.term)),
        ]:
            b = act_btn(lbl)
            b.connect('clicked', cb)
            row2.pack_start(b, False, False, 0)
        self.pack_start(row2, False, False, 0)

        self.term, sw = make_term()
        self.pack_start(sw, True, True, 6)

    def _cb(self, o, e, rc):
        term_write(self.term, (o or '') + (e or ''))

    def _build(self, _):
        term_write(self.term, '$ make  [part4]\n')
        run_bg('make', cwd=DIR4, callback=self._cb)

    def _load(self, _):
        term_write(self.term, '$ sudo insmod kbd_driver.ko && sudo chmod 666 /dev/kbd_log\n')
        run_bg('sudo insmod kbd_driver.ko && sudo chmod 666 /dev/kbd_log', cwd=DIR4, callback=self._cb)

    def _unload(self, _):
        if not ask(self.win, 'Xác nhận', 'Gỡ bỏ kbd_driver?'): return
        run_bg('sudo rmmod kbd_driver', callback=self._cb)

    def _read(self, _):
        if not os.path.exists(self.DEVICE):
            warn(self.win, 'Driver chưa được load!',
                 f'{self.DEVICE} không tồn tại. Hãy build và insmod trước.'); return
        o, e, rc = run_cmd(f'cat {self.DEVICE}')
        term_write(self.term, f'--- {self.DEVICE} ---\n' + (o or '(trống)\n'))

    def _dmesg(self, _):
        o, e, _ = run_cmd('sudo dmesg | grep -i kbd | tail -20')
        term_clear(self.term)
        term_write(self.term, o or '(không có log kbd)\n')
