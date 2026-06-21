#!/usr/bin/python3
"""
GUI cho dự án Linux Kernel - Nhóm 3 (Đề tài 24)
Entry point: import các panel từ gui_part1–4 và dựng MainWindow.
"""
import os
import stat

# Tự động cấu hình DISPLAY và XAUTHORITY cho các phiên SSH/Antigravity
if not os.environ.get('DISPLAY'):
    os.environ['DISPLAY'] = ':0'

if not os.environ.get('XAUTHORITY'):
    uid = os.getuid()
    for path in [f'/run/user/{uid}/gdm/Xauthority', os.path.expanduser('~/.Xauthority')]:
        if os.path.exists(path):
            os.environ['XAUTHORITY'] = path
            break


def auto_chmod_x(directory):
    """Tự động tìm và cấp quyền thực thi (chmod +x) cho các file cần thiết"""
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Bạn có thể thêm đuôi file khác nếu muốn, ví dụ: file.endswith(('.c', '.sh'))
            # Hoặc nếu file 'process' sau khi compile không có đuôi, ta check tên của nó:
            if file.endswith('.sh') or file == 'process':
                file_path = os.path.join(root, file)
                try:
                    # Lấy quyền hiện tại của file
                    st = os.stat(file_path)
                    # Thêm quyền thực thi cho User, Group và Others (tương đương chmod +x)
                    os.chmod(file_path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except Exception as e:
                    print(f"Không thể cấp quyền cho {file_path}: {e}")


# Lấy thư mục hiện tại của dự án và tiến hành quét
current_dir = os.path.dirname(os.path.abspath(__file__))
auto_chmod_x(current_dir)

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from gui.gui_common import CSS
from gui.gui_part1 import FileShellPanel, TaskPanel, TimePanel, InstallPanel
from gui.gui_part2 import ProcessPanel, FileCPanel, NetworkPanel
from gui.gui_part3 import KernelModulePanel
from gui.gui_part4 import KbdDriverPanel


class MainWindow(Gtk.Window):

    NAV = [
        ('file_sh', 'Quản lý File',        FileShellPanel,    'Part 1 – Shell'),
        ('task',    'Quản lý Tác vụ',      TaskPanel,         None),
        ('time',    'Quản lý Thời gian',   TimePanel,         None),
        ('install', 'Cài đặt / Gỡ cài',   InstallPanel,      None),
        ('proc',    'Quản lý Tiến trình',  ProcessPanel,      'Part 2 – C'),
        ('file_c',  'Quản lý File (C)',    FileCPanel,        None),
        ('network', 'Quản lý Mạng',       NetworkPanel,      None),
        ('kernel',  'Module Toán học',    KernelModulePanel, 'Part 3 – Module'),
        ('kbd',     'Keyboard Driver',    KbdDriverPanel,    'Part 4 – Interrupts'),
    ]

    def __init__(self):
        super().__init__(title='Linux Kernel Project – Nhóm 3 (Đề tài 24)')
        self.set_default_size(940, 600)
        self.connect('destroy', Gtk.main_quit)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(root)

        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_scroll.set_size_request(190, -1)
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar_scroll.add(sidebar)

        hdr = Gtk.Label(label='Linux Kernel\nNhóm 3 – Đề tài 24')
        hdr.set_margin_top(14); hdr.set_margin_bottom(12)
        hdr.set_justify(Gtk.Justification.CENTER)
        sidebar.pack_start(hdr, False, False, 0)
        sidebar.pack_start(Gtk.Separator(), False, False, 0)

        self.stack = Gtk.Stack()
        self.stack.set_hexpand(True); self.stack.set_vexpand(True)
        self.nav_btns = {}

        for nav_id, label, PanelCls, section in self.NAV:
            if section:
                sl = Gtk.Label(label=section)
                sl.get_style_context().add_class('section-lbl')
                sl.set_halign(Gtk.Align.START)
                sidebar.pack_start(sl, False, False, 0)

            panel = PanelCls(self)
            sw = Gtk.ScrolledWindow()
            sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            sw.add(panel)
            self.stack.add_named(sw, nav_id)

            btn = Gtk.Button(label=f'  {label}')
            btn.get_style_context().add_class('nav-btn')
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.set_halign(Gtk.Align.FILL)
            btn.connect('clicked', self._nav, nav_id)
            sidebar.pack_start(btn, False, False, 0)
            self.nav_btns[nav_id] = btn

        root.pack_start(sidebar_scroll, False, False, 0)
        root.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 0)
        root.pack_start(self.stack, True, True, 0)

        self._activate('file_sh')

    def _nav(self, _, nav_id):
        self._activate(nav_id)

    def _activate(self, nav_id):
        for nid, btn in self.nav_btns.items():
            ctx = btn.get_style_context()
            if nid == nav_id: ctx.add_class('active')
            else: ctx.remove_class('active')
        self.stack.set_visible_child_name(nav_id)


def main():
    win = MainWindow()
    win.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
