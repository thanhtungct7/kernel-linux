#!/usr/bin/python3
"""Part 2 – C programs: process, filemanagement, network"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os

from gui.gui_common import (
    DIR2,
    PROC_BIN, PROC_SRC, NET_BIN, NET_SRC, FMGMT_BIN, FMGMT_SRC,
    pipe_bin_bg, ensure_compiled,
    title_lbl, act_btn, make_term, entry,
    term_write, term_clear,
    warn, err, ask,
)


class ProcessPanel(Gtk.Box):
    """Part 2 – process.c"""
    def __init__(self, win):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.win = win
        self.pack_start(title_lbl('Quản lý Tiến trình  [process.c]'), False, False, 0)

        top = Gtk.Box(spacing=8, margin_start=12, margin_end=12, margin_top=10)
        b_list = act_btn('Liệt kê tiến trình (ps -ax)')
        b_list.connect('clicked', self._list)
        top.pack_start(b_list, False, False, 0)
        self.pack_start(top, False, False, 0)

        sig_row = Gtk.Box(spacing=8, margin_start=12, margin_end=12, margin_top=6)
        sig_row.pack_start(Gtk.Label(label='PID:'), False, False, 0)
        self.tf_pid = entry('vd: 1234')
        self.tf_pid.set_max_width_chars(10)
        sig_row.pack_start(self.tf_pid, False, False, 0)
        sig_row.pack_start(Gtk.Label(label='Signal:'), False, False, 0)
        self.tf_sig = entry('vd: 9')
        self.tf_sig.set_max_width_chars(8)
        sig_row.pack_start(self.tf_sig, False, False, 0)
        b_sig = act_btn('Gửi Signal', danger=True)
        b_sig.connect('clicked', self._signal)
        sig_row.pack_start(b_sig, False, False, 0)
        self.pack_start(sig_row, False, False, 0)

        self.term, sw = make_term()
        self.pack_start(sw, True, True, 6)

    def _ensure(self):
        ok, msg = ensure_compiled(PROC_SRC, PROC_BIN)
        if msg: term_write(self.term, msg)
        if not ok: err(self.win, 'Biên dịch thất bại', msg)
        return ok

    def _cb(self, o, e, rc):
        term_write(self.term, (o or '') + (e or ''))

    def _list(self, _):
        if not self._ensure(): return
        term_clear(self.term)
        term_write(self.term, '$ ./process  [choice 1]\n')
        pipe_bin_bg(PROC_BIN, [1, 3], cwd=DIR2, callback=self._cb)

    def _signal(self, _):
        pid = self.tf_pid.get_text().strip()
        sig = self.tf_sig.get_text().strip()
        if not pid.isdigit() or not sig.isdigit():
            warn(self.win, 'Nhập PID và số signal hợp lệ!'); return
        if not ask(self.win, 'Xác nhận', f'Gửi signal {sig} tới PID {pid}?'): return
        if not self._ensure(): return
        term_write(self.term, f'$ ./process  [choice 2: PID={pid}, sig={sig}]\n')
        pipe_bin_bg(PROC_BIN, [2, pid, sig, 3], cwd=DIR2, callback=self._cb)


class FileCPanel(Gtk.Box):
    """Part 2 – filemanagement.c"""
    def __init__(self, win):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.win = win
        self.pack_start(title_lbl('Quản lý File (C)  [filemanagement.c]'), False, False, 0)

        g = Gtk.Grid(column_spacing=8, row_spacing=6,
                     margin_start=12, margin_end=12, margin_top=10)
        g.attach(Gtk.Label(label='Thư mục:'), 0, 0, 1, 1)
        dir_box = Gtk.Box(spacing=4)
        self.tf_dir = entry(os.path.expanduser('~'))
        dir_box.pack_start(self.tf_dir, True, True, 0)
        b_browse = act_btn('Duyệt')
        b_browse.connect('clicked', self._browse)
        dir_box.pack_start(b_browse, False, False, 0)
        g.attach(dir_box, 1, 0, 1, 1)
        g.attach(Gtk.Label(label='Tên file:'), 0, 1, 1, 1)
        file_box = Gtk.Box(spacing=4)
        self.tf_file = entry('vd: test.txt')
        file_box.pack_start(self.tf_file, True, True, 0)
        b_browse_file = act_btn('Duyệt')
        b_browse_file.connect('clicked', self._browse_file)
        file_box.pack_start(b_browse_file, False, False, 0)
        g.attach(file_box, 1, 1, 1, 1)
        self.pack_start(g, False, False, 0)

        btn_row1 = Gtk.Box(spacing=6, margin_start=12, margin_end=12, margin_top=6)
        for lbl, cb in [
            ('Liệt kê',      self._list),
            ('Tạo mới',      self._create_new),
            ('Xem nội dung', self._show),
            ('Đổi tên',      self._rename),
        ]:
            b = act_btn(lbl)
            b.connect('clicked', cb)
            btn_row1.pack_start(b, False, False, 0)
        self.pack_start(btn_row1, False, False, 0)

        btn_row2 = Gtk.Box(spacing=6, margin_start=12, margin_end=12, margin_top=4)
        b_trash = act_btn('Xóa → Thùng rác (.trash)')
        b_trash.connect('clicked', self._delete_trash)
        btn_row2.pack_start(b_trash, False, False, 0)
        b_perm = act_btn('Xóa vĩnh viễn', danger=True)
        b_perm.connect('clicked', self._delete_perm)
        btn_row2.pack_start(b_perm, False, False, 0)
        self.pack_start(btn_row2, False, False, 0)

        self.term, sw = make_term()
        self.pack_start(sw, True, True, 6)

    def _fname(self): return self.tf_file.get_text().strip()
    def _cwd(self):   return self.tf_dir.get_text().strip() or os.path.expanduser('~')

    def _fullpath(self, name):
        return name if os.path.isabs(name) else os.path.join(self._cwd(), name)

    def _browse(self, _):
        dlg = Gtk.FileChooserDialog(title='Chọn thư mục', parent=self.win,
                                    action=Gtk.FileChooserAction.SELECT_FOLDER)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dlg.set_current_folder(self._cwd())
        if dlg.run() == Gtk.ResponseType.OK:
            self.tf_dir.set_text(dlg.get_filename())
        dlg.destroy()

    def _browse_file(self, _):
        dlg = Gtk.FileChooserDialog(title='Chọn file', parent=self.win,
                                    action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        cwd = self._cwd()
        if os.path.isdir(cwd):
            dlg.set_current_folder(cwd)
        if dlg.run() == Gtk.ResponseType.OK:
            filepath = dlg.get_filename()
            try:
                rel = os.path.relpath(filepath, cwd)
            except ValueError:
                rel = filepath
            self.tf_file.set_text(rel)
        dlg.destroy()

    def _ensure(self):
        ok, msg = ensure_compiled(FMGMT_SRC, FMGMT_BIN)
        if msg: term_write(self.term, msg)
        if not ok: err(self.win, 'Biên dịch thất bại', msg)
        return ok

    def _cb(self, o, e, rc):
        term_write(self.term, (o or '') + (e or ''))

    def _list(self, _):
        if not self._ensure(): return
        term_clear(self.term)
        d = self._cwd()
        term_write(self.term, f'$ ./filemanagement  [list: {d}]\n')
        pipe_bin_bg(FMGMT_BIN, [1, d, 5], cwd=DIR2, callback=self._cb)

    def _create_new(self, _):
        dlg = Gtk.Dialog(title='Tạo mới', transient_for=self.win, modal=True)
        dlg.add_buttons('Hủy', Gtk.ResponseType.CANCEL, 'Tạo', Gtk.ResponseType.OK)
        area = dlg.get_content_area()
        area.set_spacing(8)
        area.set_margin_start(14); area.set_margin_end(14)
        area.set_margin_top(10);   area.set_margin_bottom(10)
        rb_file = Gtk.RadioButton.new_with_label(None, 'File mới')
        rb_dir  = Gtk.RadioButton.new_with_label_from_widget(rb_file, 'Thư mục mới (Folder)')
        area.pack_start(rb_file, False, False, 0)
        area.pack_start(rb_dir,  False, False, 0)
        hbox = Gtk.Box(spacing=6)
        hbox.pack_start(Gtk.Label(label='Tên:'), False, False, 0)
        tf = Gtk.Entry()
        tf.set_placeholder_text('vd: myfile.txt  hoặc  myfolder')
        tf.set_hexpand(True)
        hbox.pack_start(tf, True, True, 0)
        area.pack_start(hbox, False, False, 0)
        dlg.show_all()
        resp = dlg.run()
        name   = tf.get_text().strip()
        is_dir = rb_dir.get_active()
        dlg.destroy()
        if resp != Gtk.ResponseType.OK or not name:
            return
        if not self._ensure(): return
        fullpath = os.path.join(self._cwd(), name)
        if is_dir:
            term_write(self.term, f'$ ./filemanagement  [mkdir: {name}]\n')
            pipe_bin_bg(FMGMT_BIN, [6, fullpath, 5], cwd=DIR2, callback=self._cb)
        else:
            term_write(self.term, f'$ ./filemanagement  [create file: {name}]\n')
            pipe_bin_bg(FMGMT_BIN, [2, fullpath, 5], cwd=DIR2, callback=self._cb)

    def _show(self, _):
        f = self._fname()
        if not f: warn(self.win, 'Nhập tên file!'); return
        if not self._ensure(): return
        term_clear(self.term)
        term_write(self.term, f'$ ./filemanagement  [show: {f}]\n')
        pipe_bin_bg(FMGMT_BIN, [4, self._fullpath(f), 5], cwd=DIR2, callback=self._cb)

    def _rename(self, _):
        f = self._fname()
        if not f: warn(self.win, 'Nhập tên file cần đổi tên!'); return
        dlg = Gtk.Dialog(title='Đổi tên', transient_for=self.win, modal=True)
        dlg.add_buttons('Hủy', Gtk.ResponseType.CANCEL, 'Đổi tên', Gtk.ResponseType.OK)
        area = dlg.get_content_area()
        area.set_spacing(8)
        area.set_margin_start(14); area.set_margin_end(14)
        area.set_margin_top(10);   area.set_margin_bottom(10)
        area.pack_start(Gtk.Label(label=f'Đổi tên: {f}'), False, False, 0)
        hbox = Gtk.Box(spacing=6)
        hbox.pack_start(Gtk.Label(label='Tên mới:'), False, False, 0)
        tf = Gtk.Entry()
        tf.set_text(os.path.basename(f))
        tf.set_hexpand(True)
        tf.select_region(0, -1)
        hbox.pack_start(tf, True, True, 0)
        area.pack_start(hbox, False, False, 0)
        dlg.show_all()
        resp     = dlg.run()
        new_name = tf.get_text().strip()
        dlg.destroy()
        if resp != Gtk.ResponseType.OK or not new_name:
            return
        if new_name == os.path.basename(f):
            return
        old_path = self._fullpath(f)
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        if not self._ensure(): return
        term_clear(self.term)
        term_write(self.term, f'$ ./filemanagement  [rename: {f} → {new_name}]\n')
        pipe_bin_bg(FMGMT_BIN, [7, old_path, new_path, 5], cwd=DIR2, callback=self._cb)

    def _delete_trash(self, _):
        f = self._fname()
        if not f: warn(self.win, 'Nhập tên file cần xóa!'); return
        trash_dir = os.path.join(self._cwd(), '.trash')
        if not ask(self.win, 'Chuyển vào thùng rác?',
                   f'Di chuyển "{f}" vào\n{trash_dir}'): return
        if not self._ensure(): return
        term_write(self.term, f'$ ./filemanagement  [trash: {f}]\n')
        pipe_bin_bg(FMGMT_BIN, [8, self._fullpath(f), trash_dir, 5],
                    cwd=DIR2, callback=self._cb)

    def _delete_perm(self, _):
        f = self._fname()
        if not f: warn(self.win, 'Nhập tên file cần xóa!'); return
        if not ask(self.win, 'Xóa vĩnh viễn?',
                   f'Xóa vĩnh viễn "{f}"?\nHành động này KHÔNG thể hoàn tác!'): return
        if not self._ensure(): return
        term_write(self.term, f'$ ./filemanagement  [delete perm: {f}]\n')
        pipe_bin_bg(FMGMT_BIN, [9, self._fullpath(f), 5], cwd=DIR2, callback=self._cb)


class NetworkPanel(Gtk.Box):
    """Part 2 – network.c"""
    def __init__(self, win):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.win = win
        self.pack_start(title_lbl('Quản lý Mạng  [network.c]'), False, False, 0)

        top = Gtk.Box(spacing=8, margin_start=12, margin_end=12, margin_top=10)
        b_list = act_btn('Liệt kê giao diện mạng')
        b_list.connect('clicked', self._list)
        top.pack_start(b_list, False, False, 0)
        self.pack_start(top, False, False, 0)

        iface_row = Gtk.Box(spacing=8, margin_start=12, margin_end=12, margin_top=8)
        iface_row.pack_start(Gtk.Label(label='Giao diện:'), False, False, 0)
        self.tf_iface = entry('vd: eth0')
        iface_row.pack_start(self.tf_iface, True, True, 0)
        b_en  = act_btn('Bật (sudo)')
        b_en.connect('clicked', self._enable)
        b_dis = act_btn('Tắt (sudo)', danger=True)
        b_dis.connect('clicked', self._disable)
        iface_row.pack_start(b_en, False, False, 0)
        iface_row.pack_start(b_dis, False, False, 0)
        self.pack_start(iface_row, False, False, 0)

        ip_row = Gtk.Box(spacing=8, margin_start=12, margin_end=12, margin_top=6)
        ip_row.pack_start(Gtk.Label(label='IP mới (CIDR):'), False, False, 0)
        self.tf_ip = entry('vd: 192.168.1.100/24')
        ip_row.pack_start(self.tf_ip, True, True, 0)
        b_ip = act_btn('Đổi IP (sudo)')
        b_ip.connect('clicked', self._change_ip)
        ip_row.pack_start(b_ip, False, False, 0)
        self.pack_start(ip_row, False, False, 0)

        self.term, sw = make_term()
        self.pack_start(sw, True, True, 6)

    def _iface(self): return self.tf_iface.get_text().strip()

    def _ensure(self):
        ok, msg = ensure_compiled(NET_SRC, NET_BIN)
        if msg: term_write(self.term, msg)
        if not ok: err(self.win, 'Biên dịch thất bại', msg)
        return ok

    def _cb(self, o, e, rc):
        term_write(self.term, (o or '') + (e or ''))

    def _list(self, _):
        if not self._ensure(): return
        term_clear(self.term)
        term_write(self.term, '$ ./network  [choice 1]\n')
        pipe_bin_bg(NET_BIN, [1, 5], cwd=DIR2, sudo=True, callback=self._cb)

    def _enable(self, _):
        i = self._iface()
        if not i: warn(self.win, 'Nhập tên giao diện!'); return
        if not self._ensure(): return
        term_write(self.term, f'$ ./network  [choice 2: {i}]\n')
        pipe_bin_bg(NET_BIN, [2, i, 5], cwd=DIR2, sudo=True, callback=self._cb)

    def _disable(self, _):
        i = self._iface()
        if not i: warn(self.win, 'Nhập tên giao diện!'); return
        if not ask(self.win, 'Xác nhận', f'Tắt giao diện {i}?'): return
        if not self._ensure(): return
        term_write(self.term, f'$ ./network  [choice 3: {i}]\n')
        pipe_bin_bg(NET_BIN, [3, i, 5], cwd=DIR2, sudo=True, callback=self._cb)

    def _change_ip(self, _):
        i = self._iface()
        ip = self.tf_ip.get_text().strip()
        if not i or not ip: warn(self.win, 'Nhập giao diện và địa chỉ IP!'); return
        if not self._ensure(): return
        term_write(self.term, f'$ ./network  [choice 4: {i} → {ip}]\n')
        pipe_bin_bg(NET_BIN, [4, i, ip, 5], cwd=DIR2, sudo=True, callback=self._cb)
