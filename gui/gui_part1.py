#!/usr/bin/python3
"""Part 1 – Shell scripts: filemanagement, taskmanagement, timemanagement, installanduninstall"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os, tempfile

from gui.gui_common import (
    FILE_SH, TASK_SH, TIME_SH, INST_SH,
    pipe_sh_bg, run_bg,
    title_lbl, act_btn, make_term, entry, tv_text,
    term_write, term_clear,
    warn, err, ask, info,
)


class FileShellPanel(Gtk.Box):
    """Part 1 – filemanagement.sh"""
    def __init__(self, win):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.win = win
        self.pack_start(title_lbl('Quản lý File  [filemanagement.sh]'), False, False, 0)

        top = Gtk.Box(spacing=8, margin_start=12, margin_end=12, margin_top=10)
        top.pack_start(Gtk.Label(label='Thư mục làm việc:'), False, False, 0)
        self.tf_dir = entry(os.path.expanduser('~'))
        top.pack_start(self.tf_dir, True, True, 0)
        b = act_btn('Duyệt')
        b.connect('clicked', self._browse)
        top.pack_start(b, False, False, 0)
        self.pack_start(top, False, False, 0)

        file_row = Gtk.Box(spacing=8, margin_start=12, margin_end=12, margin_top=6)
        file_row.pack_start(Gtk.Label(label='Tên file:'), False, False, 0)
        self.tf_file = entry('vd: test.txt')
        file_row.pack_start(self.tf_file, True, True, 0)
        b_browse_file = act_btn('Duyệt')
        b_browse_file.connect('clicked', self._browse_file)
        file_row.pack_start(b_browse_file, False, False, 0)
        self.pack_start(file_row, False, False, 0)

        btn_row = Gtk.Box(spacing=6, margin_start=12, margin_end=12, margin_top=6)
        for label, cb, danger in [
            ('Liệt kê',  self._list,   False),
            ('Tạo file', self._create, False),
            ('Xem',      self._show,   False),
            ('Đổi tên',  self._rename, False),
            ('Copy',     self._copy,   False),
            ('Xóa',      self._remove, True),
        ]:
            b2 = act_btn(label, danger=danger)
            b2.connect('clicked', cb)
            btn_row.pack_start(b2, False, False, 0)
        self.pack_start(btn_row, False, False, 0)

        self.view_stack = Gtk.Stack()
        self.view_stack.set_hexpand(True)
        self.view_stack.set_vexpand(True)

        self.term, term_sw = make_term()
        self.view_stack.add_named(term_sw, 'term')

        editor_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.editor_tv = Gtk.TextView()
        self.editor_tv.set_wrap_mode(Gtk.WrapMode.CHAR)
        self.editor_tv.get_style_context().add_class('term')
        editor_sw = Gtk.ScrolledWindow()
        editor_sw.set_hexpand(True); editor_sw.set_vexpand(True)
        editor_sw.set_min_content_height(160)
        editor_sw.add(self.editor_tv)
        editor_box.pack_start(editor_sw, True, True, 0)

        edit_btns = Gtk.Box(spacing=6,
                            margin_start=8, margin_end=8,
                            margin_top=4, margin_bottom=4)
        self.lbl_editing = Gtk.Label(label='')
        self.lbl_editing.get_style_context().add_class('section-lbl')
        self.lbl_editing.set_hexpand(True)
        self.lbl_editing.set_halign(Gtk.Align.START)
        edit_btns.pack_start(self.lbl_editing, True, True, 0)
        b_save = act_btn('Lưu file')
        b_save.connect('clicked', self._save_edit)
        b_close_ed = act_btn('Đóng')
        b_close_ed.connect('clicked', lambda _: self._to_term())
        edit_btns.pack_start(b_save, False, False, 0)
        edit_btns.pack_start(b_close_ed, False, False, 0)
        editor_box.pack_start(edit_btns, False, False, 0)

        self.view_stack.add_named(editor_box, 'editor')
        self.pack_start(self.view_stack, True, True, 6)
        self._edit_file = None

    def _cwd(self): return self.tf_dir.get_text().strip() or os.path.expanduser('~')
    def _fname(self): return self.tf_file.get_text().strip()

    def _browse(self, _):
        dlg = Gtk.FileChooserDialog(title='Chọn thư mục', parent=self.win,
                                    action=Gtk.FileChooserAction.SELECT_FOLDER)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
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

    def _cb(self, o, e, rc):
        term_write(self.term, (o or '') + (e or ''))

    def _to_term(self):
        self.view_stack.set_visible_child_name('term')

    def _to_editor(self, filepath):
        self._edit_file = filepath
        self.lbl_editing.set_text(f'Đang chỉnh: {os.path.basename(filepath)}')
        self.view_stack.set_visible_child_name('editor')

    def _save_edit(self, _):
        if not self._edit_file:
            return
        buf = self.editor_tv.get_buffer()
        content = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        try:
            fd, tmp_path = tempfile.mkstemp()
            with os.fdopen(fd, 'w') as fh:
                fh.write(content)
        except Exception as ex:
            err(self.win, 'Lỗi tạo file tạm', str(ex)); return
        self._to_term()
        term_clear(self.term)
        term_write(self.term, f'$ bash filemanagement.sh  [save: {self._edit_file}]\n')
        pipe_sh_bg(FILE_SH, [9, tmp_path, self._edit_file, 0],
                   callback=self._cb_save)

    def _list(self, _):
        self._to_term()
        term_clear(self.term)
        term_write(self.term, f'$ bash filemanagement.sh  [cwd: {self._cwd()}]\n')
        pipe_sh_bg(FILE_SH, [1, 0], cwd=self._cwd(), callback=self._cb)

    def _create(self, _):
        f = self._fname()
        if not f: warn(self.win, 'Nhập tên file!'); return
        self._to_term()
        term_write(self.term, f'$ bash filemanagement.sh  [create: {f}]\n')
        pipe_sh_bg(FILE_SH, [2, f, 0], cwd=self._cwd(), callback=self._cb)

    def _cb_save(self, o, e, rc):
        if rc == 0:
            term_write(self.term, f'Đã lưu: {self._edit_file}\n')
        else:
            GLib.idle_add(err, self.win, 'Lỗi lưu file', e or 'Lỗi không xác định')

    def _cb_show(self, o, e, rc):
        content = o or ''
        GLib.idle_add(self._open_editor_with, content)

    def _open_editor_with(self, content):
        self.editor_tv.get_buffer().set_text(content)
        self._to_editor(os.path.join(self._cwd(), self._fname()))

    def _show(self, _):
        f = self._fname()
        if not f: warn(self.win, 'Nhập tên file!'); return
        pipe_sh_bg(FILE_SH, [8, f, 0], cwd=self._cwd(), callback=self._cb_show)

    def _rename(self, _):
        f = self._fname()
        if not f: warn(self.win, 'Nhập tên file!'); return
        cwd = self._cwd()
        dlg = Gtk.FileChooserDialog(title=f'Đổi tên "{f}"',
                                    transient_for=self.win, modal=True,
                                    action=Gtk.FileChooserAction.SAVE)
        dlg.add_buttons('Hủy', Gtk.ResponseType.CANCEL,
                        'Đổi tên', Gtk.ResponseType.OK)
        dlg.set_do_overwrite_confirmation(True)
        if os.path.isdir(cwd):
            dlg.set_current_folder(cwd)
        dlg.set_current_name(f)
        resp = dlg.run()
        new_path = dlg.get_filename()
        dlg.destroy()
        if resp != Gtk.ResponseType.OK or not new_path:
            return
        new_name = os.path.basename(new_path)
        if new_name == f:
            return
        term_clear(self.term)
        term_write(self.term, f'$ bash filemanagement.sh  [rename: {f} → {new_name}]\n')
        pipe_sh_bg(FILE_SH, [6, f, new_name, 0], cwd=cwd, callback=self._cb)

    def _copy(self, _):
        f = self._fname()
        if not f: warn(self.win, 'Nhập tên file!'); return
        dlg = Gtk.FileChooserDialog(title=f'Sao chép "{f}" đến…',
                                    transient_for=self.win, modal=True,
                                    action=Gtk.FileChooserAction.SELECT_FOLDER)
        dlg.add_buttons('Hủy', Gtk.ResponseType.CANCEL,
                        'Sao chép vào đây', Gtk.ResponseType.OK)
        cwd = self._cwd()
        if os.path.isdir(cwd):
            dlg.set_current_folder(cwd)
        resp = dlg.run()
        dest_dir = dlg.get_filename()
        dlg.destroy()
        if resp != Gtk.ResponseType.OK or not dest_dir:
            return
        dest_path = os.path.join(dest_dir, os.path.basename(f))
        term_clear(self.term)
        term_write(self.term, f'$ bash filemanagement.sh  [copy: {f} → {dest_path}]\n')
        pipe_sh_bg(FILE_SH, [7, f, dest_path, 0], cwd=cwd, callback=self._cb)

    def _remove(self, _):
        f = self._fname()
        if not f: warn(self.win, 'Nhập tên file!'); return
        if not ask(self.win, 'Xác nhận xóa', f'Xóa: {f}?'): return
        self._to_term()
        term_write(self.term, f'$ bash filemanagement.sh  [remove: {f}]\n')
        pipe_sh_bg(FILE_SH, [3, f, 0], cwd=self._cwd(), callback=self._cb)


class TaskPanel(Gtk.Box):
    """Part 1 – taskmanagement.sh"""
    def __init__(self, win):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.win = win
        self.pack_start(title_lbl('Quản lý Tác vụ  [taskmanagement.sh]'), False, False, 0)

        g = Gtk.Grid(column_spacing=8, row_spacing=6,
                     margin_start=12, margin_end=12, margin_top=10)
        g.attach(Gtk.Label(label='Lệnh thực thi:'), 0, 0, 1, 1)
        self.tf_cmd = entry('vd: /usr/bin/backup.sh')
        g.attach(self.tf_cmd, 1, 0, 1, 1)
        g.attach(Gtk.Label(label='Lịch (cron):'), 0, 1, 1, 1)
        self.tf_sched = entry('vd: 0 2 * * *')
        g.attach(self.tf_sched, 1, 1, 1, 1)
        g.attach(Gtk.Label(label='Số thứ tự:'), 0, 2, 1, 1)
        self.tf_idx = entry('vd: 1  (để sửa/xóa)')
        g.attach(self.tf_idx, 1, 2, 1, 1)
        self.pack_start(g, False, False, 0)

        btn_row = Gtk.Box(spacing=6, margin_start=12, margin_end=12, margin_top=6)
        for lbl, cb, danger in [
            ('Liệt kê',    self._list,   False),
            ('Tạo tác vụ', self._create, False),
            ('Sửa tác vụ', self._edit,   False),
            ('Xóa tác vụ', self._delete, True),
        ]:
            b = act_btn(lbl, danger=danger)
            b.connect('clicked', cb)
            btn_row.pack_start(b, False, False, 0)

        help_btn = Gtk.Button(label='?')
        help_btn.set_tooltip_text(
            'Hướng dẫn quản lý tác vụ (cron job)\n'
            '\n'
            'Lệnh thực thi: lệnh hoặc đường dẫn script cần chạy\n'
            '  vd: /usr/bin/backup.sh\n'
            '  vd: rm -rf /tmp/*\n'
            '\n'
            'Lịch (cron): 5 trường cách nhau bằng dấu cách\n'
            '  phút  giờ  ngày  tháng  thứ\n'
            '  (* = mọi giá trị)\n'
            '\n'
            '  0 2 * * *      → 2h sáng mỗi ngày\n'
            '  30 8 * * 1     → 8h30 mỗi thứ Hai\n'
            '  */5 * * * *    → mỗi 5 phút\n'
            '  0 0 1 * *      → nửa đêm ngày 1 mỗi tháng\n'
            '\n'
            'Số thứ tự: dùng khi Sửa hoặc Xóa tác vụ\n'
            '  (xem số thứ tự bằng nút Liệt kê)'
        )
        btn_row.pack_end(help_btn, False, False, 0)
        self.pack_start(btn_row, False, False, 0)

        self.term, sw = make_term()
        self.pack_start(sw, True, True, 6)

    def _cb(self, o, e, rc):
        term_write(self.term, (o or '') + (e or ''))

    def _list(self, _):
        term_clear(self.term)
        term_write(self.term, '$ bash taskmanagement.sh  [list]\n')
        pipe_sh_bg(TASK_SH, [1, 5], callback=self._cb)

    def _create(self, _):
        cmd = self.tf_cmd.get_text().strip()
        sched = self.tf_sched.get_text().strip()
        if not cmd or not sched: warn(self.win, 'Nhập lệnh và lịch trình!'); return
        term_write(self.term, f'$ bash taskmanagement.sh  [create: {sched} {cmd}]\n')
        pipe_sh_bg(TASK_SH, [2, cmd, sched, 5], callback=self._cb)

    def _edit(self, _):
        idx = self.tf_idx.get_text().strip()
        cmd = self.tf_cmd.get_text().strip()
        sched = self.tf_sched.get_text().strip()
        if not idx.isdigit() or not cmd or not sched:
            warn(self.win, 'Nhập đầy đủ số thứ tự, lệnh và lịch!'); return
        term_write(self.term, f'$ bash taskmanagement.sh  [edit dòng {idx}]\n')
        pipe_sh_bg(TASK_SH, [3, idx, cmd, sched, 5], callback=self._cb)

    def _delete(self, _):
        idx = self.tf_idx.get_text().strip()
        if not idx.isdigit(): warn(self.win, 'Nhập số thứ tự hợp lệ!'); return
        if not ask(self.win, 'Xác nhận xóa', f'Xóa tác vụ số {idx}?'): return
        term_write(self.term, f'$ bash taskmanagement.sh  [delete dòng {idx}]\n')
        pipe_sh_bg(TASK_SH, [4, idx, 5], callback=self._cb)


class TimePanel(Gtk.Box):
    """Part 1 – timemanagement.sh"""
    def __init__(self, win):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.win = win
        self.pack_start(title_lbl('Quản lý Thời gian  [timemanagement.sh]'), False, False, 0)

        g = Gtk.Grid(column_spacing=10, row_spacing=10,
                     margin_start=16, margin_end=16, margin_top=16)
        self.pack_start(g, False, False, 0)

        b1 = act_btn('Xem giờ hiện tại (Asia/Ho_Chi_Minh)')
        b1.connect('clicked', self._show)
        g.attach(b1, 0, 0, 3, 1)

        g.attach(Gtk.Label(label='Đặt giờ (hh:mm:ss):'), 0, 1, 1, 1)
        self.tf_time = entry('vd: 14:30:00')
        g.attach(self.tf_time, 1, 1, 1, 1)
        b2 = act_btn('Đặt giờ (root)')
        b2.connect('clicked', self._set_hour)
        g.attach(b2, 2, 1, 1, 1)

        g.attach(Gtk.Label(label='Đặt ngày (yyyy-mm-dd):'), 0, 2, 1, 1)
        self.tf_date = entry('vd: 2025-06-16')
        g.attach(self.tf_date, 1, 2, 1, 1)
        b3 = act_btn('Đặt ngày (root)')
        b3.connect('clicked', self._set_date)
        g.attach(b3, 2, 2, 1, 1)

        b4 = act_btn('Đồng bộ NTP tự động (root)')
        b4.connect('clicked', self._ntp)
        g.attach(b4, 0, 3, 3, 1)

        self.term, sw = make_term()
        self.pack_start(sw, True, True, 6)

    def _cb(self, o, e, rc):
        term_write(self.term, (o or '') + (e or ''))

    def _show(self, _):
        term_write(self.term, '$ bash timemanagement.sh  [choice 1]\n')
        pipe_sh_bg(TIME_SH, [1, 5], callback=self._cb)

    def _set_hour(self, _):
        t = self.tf_time.get_text().strip()
        if not t: warn(self.win, 'Nhập giờ!'); return
        term_write(self.term, f'$ bash timemanagement.sh  [choice 2: {t}]\n')
        pipe_sh_bg(TIME_SH, [2, t, 5], callback=self._cb)

    def _set_date(self, _):
        d = self.tf_date.get_text().strip()
        if not d: warn(self.win, 'Nhập ngày!'); return
        term_write(self.term, f'$ bash timemanagement.sh  [choice 3: {d}]\n')
        pipe_sh_bg(TIME_SH, [3, d, 5], callback=self._cb)

    def _ntp(self, _):
        term_write(self.term, '$ bash timemanagement.sh  [choice 4 – NTP]\n')
        pipe_sh_bg(TIME_SH, [4, 5], callback=self._cb)


class InstallPanel(Gtk.Box):
    """Part 1 – installanduninstall.sh"""
    def __init__(self, win):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.win = win
        self.input_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'part1', 'input.txt')
        self.pack_start(title_lbl('Cài đặt / Gỡ cài đặt  [installanduninstall.sh]'), False, False, 0)

        lbl = Gtk.Label(label=f'Danh sách gói ({self.input_file}):')
        lbl.set_halign(Gtk.Align.START)
        lbl.set_margin_start(12); lbl.set_margin_top(8)
        self.pack_start(lbl, False, False, 0)

        self.tv_pkgs = Gtk.TextView()
        self.tv_pkgs.set_wrap_mode(Gtk.WrapMode.WORD)
        sw_pkg = Gtk.ScrolledWindow()
        sw_pkg.set_min_content_height(80)
        sw_pkg.set_margin_start(12); sw_pkg.set_margin_end(12)
        sw_pkg.add(self.tv_pkgs)
        self.pack_start(sw_pkg, False, False, 0)

        btn_row = Gtk.Box(spacing=8, margin_start=12, margin_end=12, margin_top=6)
        for lbl2, cb, danger in [
            ('Tải input.txt',     self._load,      False),
            ('Lưu input.txt',     self._save,      False),
            ('Cài đặt (sudo)',    self._install,   False),
            ('Gỡ cài đặt (sudo)', self._uninstall, True),
        ]:
            b = act_btn(lbl2, danger=danger)
            b.connect('clicked', cb)
            btn_row.pack_start(b, False, False, 0)
        self.pack_start(btn_row, False, False, 0)

        self.term, sw2 = make_term()
        self.pack_start(sw2, True, True, 6)
        self._load(None)

    def _load(self, _):
        try:
            with open(self.input_file) as f:
                self.tv_pkgs.get_buffer().set_text(f.read())
        except FileNotFoundError:
            self.tv_pkgs.get_buffer().set_text('')

    def _save(self, _):
        try:
            with open(self.input_file, 'w') as f:
                f.write(tv_text(self.tv_pkgs))
        except Exception as ex:
            err(self.win, 'Lỗi lưu file', str(ex))

    def _cb(self, o, e, rc):
        term_write(self.term, (o or '') + (e or ''))

    def _install(self, _):
        self._save(None)
        term_write(self.term, '$ bash installanduninstall.sh install\n')
        run_bg(f'bash "{INST_SH}" install',
               cwd=os.path.dirname(INST_SH), callback=self._cb)

    def _uninstall(self, _):
        if not ask(self.win, 'Xác nhận', 'Gỡ bỏ tất cả gói trong input.txt?'): return
        self._save(None)
        term_write(self.term, '$ bash installanduninstall.sh uninstall\n')
        run_bg(f'bash "{INST_SH}" uninstall',
               cwd=os.path.dirname(INST_SH), callback=self._cb)
