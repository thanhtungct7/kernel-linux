#!/usr/bin/python3
"""Part 2 – C programs: process, filemanagement, network"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os
import struct
import socket
import threading
import time
import subprocess

from gui.gui_common import (
    DIR2,
    PROC_BIN, PROC_SRC, NET_BIN, NET_SRC, FMGMT_BIN, FMGMT_SRC,
    SOCKET_DIR, SOCKET_SRV_SRC, SOCKET_SRV_BIN, SOCKET_CLI_SRC, SOCKET_CLI_BIN,
    open_terminal,
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


# Cấu trúc gói tin Socket Part 2 (1400 bytes)
MSG_PACKET_FORMAT = "=i100s1024si256siii"
MSG_PACKET_SIZE = struct.calcsize(MSG_PACKET_FORMAT)
MSG_TYPE_CHAT = 1
MSG_TYPE_FILE = 2
FILE_CHUNK_SIZE = 1024

def pack_msg(msg_type, sender, content, bytes_read=0, filename="", filesize=0, chunk_id=0, total_chunks=0):
    sender_b = sender.encode('utf-8')[:99] + b'\x00'
    sender_b = sender_b.ljust(100, b'\x00')
    
    if isinstance(content, str):
        content_b = content.encode('utf-8')[:1023] + b'\x00'
    else:
        content_b = content[:1024]
    content_b = content_b.ljust(1024, b'\x00')
    
    filename_b = filename.encode('utf-8')[:255] + b'\x00'
    filename_b = filename_b.ljust(256, b'\x00')
    
    return struct.pack(MSG_PACKET_FORMAT, msg_type, sender_b, content_b, bytes_read, filename_b, filesize, chunk_id, total_chunks)

def unpack_msg(data):
    msg_type, sender_b, content_b, bytes_read, filename_b, filesize, chunk_id, total_chunks = struct.unpack(MSG_PACKET_FORMAT, data)
    
    sender = sender_b.split(b'\x00')[0].decode('utf-8', errors='ignore')
    
    if msg_type == MSG_TYPE_CHAT:
        content = content_b.split(b'\x00')[0].decode('utf-8', errors='ignore')
    else:
        content = content_b[:bytes_read]
        
    filename = filename_b.split(b'\x00')[0].decode('utf-8', errors='ignore')
    
    return {
        'type': msg_type,
        'sender': sender,
        'content': content,
        'bytes_read': bytes_read,
        'filename': filename,
        'filesize': filesize,
        'chunk_id': chunk_id,
        'total_chunks': total_chunks
    }


class SocketPanel(Gtk.Box):
    """Part 2 – socket/server.c and socket/client.c (Native GUI Version)"""
    def __init__(self, win):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.win = win
        self.pack_start(title_lbl('Truyền thông Socket  [socket part2]'), False, False, 0)
        
        # Trạng thái kết nối và tiến trình
        self.server_proc = None
        self.client_socket = None
        self.connected = False
        self.incoming_files = {}  # key: (sender, filename) -> {file, received, total}

        # Bố cục chính nằm ngang: Bên trái cấu hình, bên phải phòng chat
        main_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, margin_start=12, margin_end=12, margin_top=8)
        self.pack_start(main_hbox, True, True, 0)

        # ── CỘT BÊN TRÁI: Cấu hình và Log Hệ thống ───────────────────────────
        left_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        left_vbox.set_size_request(280, -1)
        main_hbox.pack_start(left_vbox, False, False, 0)

        # Khung Server
        srv_frame = Gtk.Frame(label=' Cấu hình Server ')
        srv_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_start=10, margin_end=10, margin_top=8, margin_bottom=8)
        
        srv_grid = Gtk.Grid(column_spacing=6, row_spacing=6)
        srv_grid.attach(Gtk.Label(label='Port Server:'), 0, 0, 1, 1)
        self.tf_srv_port = entry('2000')
        self.tf_srv_port.set_text('2000')
        self.tf_srv_port.set_max_width_chars(8)
        srv_grid.attach(self.tf_srv_port, 1, 0, 1, 1)
        srv_vbox.pack_start(srv_grid, False, False, 0)
        
        self.btn_srv = act_btn('Khởi chạy Server')
        self.btn_srv.connect('clicked', self._toggle_server)
        srv_vbox.pack_start(self.btn_srv, False, False, 0)
        srv_frame.add(srv_vbox)
        left_vbox.pack_start(srv_frame, False, False, 0)

        # Khung Client
        cli_frame = Gtk.Frame(label=' Cấu hình Client ')
        cli_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_start=10, margin_end=10, margin_top=8, margin_bottom=8)
        
        cli_grid = Gtk.Grid(column_spacing=6, row_spacing=6)
        cli_grid.attach(Gtk.Label(label='IP Server:'), 0, 0, 1, 1)
        self.tf_cli_ip = entry('127.0.0.1')
        self.tf_cli_ip.set_text('127.0.0.1')
        cli_grid.attach(self.tf_cli_ip, 1, 0, 1, 1)

        cli_grid.attach(Gtk.Label(label='Port Client:'), 0, 1, 1, 1)
        self.tf_cli_port = entry('2000')
        self.tf_cli_port.set_text('2000')
        cli_grid.attach(self.tf_cli_port, 1, 1, 1, 1)

        cli_grid.attach(Gtk.Label(label='Tên User:'), 0, 2, 1, 1)
        self.tf_cli_user = entry('Client1')
        self.tf_cli_user.set_text('Client1')
        cli_grid.attach(self.tf_cli_user, 1, 2, 1, 1)
        cli_vbox.pack_start(cli_grid, False, False, 0)

        self.btn_cli = act_btn('Kết nối')
        self.btn_cli.connect('clicked', self._toggle_client)
        cli_vbox.pack_start(self.btn_cli, False, False, 0)
        cli_frame.add(cli_vbox)
        left_vbox.pack_start(cli_frame, False, False, 0)

        # Terminal Nhật ký
        left_vbox.pack_start(Gtk.Label(label='Nhật ký hệ thống:'), False, False, 0)
        self.term, sw_term = make_term()
        sw_term.set_min_content_height(120)
        left_vbox.pack_start(sw_term, True, True, 0)

        # ── CỘT BÊN PHẢI: Giao diện Phòng Chat ──────────────────────────────
        chat_frame = Gtk.Frame(label=' Phòng Chat nhóm ')
        main_hbox.pack_start(chat_frame, True, True, 0)

        chat_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_start=10, margin_end=10, margin_top=8, margin_bottom=8)
        chat_frame.add(chat_vbox)

        # Khung hiển thị tin nhắn (Scrolled Window + TextView)
        self.chat_tv = Gtk.TextView()
        self.chat_tv.set_editable(False)
        self.chat_tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.chat_tv.get_style_context().add_class('term') # Dùng nền đen, chữ xanh đồng bộ terminal
        
        sw_chat = Gtk.ScrolledWindow()
        sw_chat.set_hexpand(True)
        sw_chat.set_vexpand(True)
        sw_chat.add(self.chat_tv)
        chat_vbox.pack_start(sw_chat, True, True, 0)

        # Khung nhập liệu ở dưới cùng
        input_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        chat_vbox.pack_start(input_hbox, False, False, 0)

        self.tf_msg = entry('Nhập nội dung chat...')
        self.tf_msg.connect('activate', self._on_send_msg)
        input_hbox.pack_start(self.tf_msg, True, True, 0)

        self.btn_send = act_btn('Gửi')
        self.btn_send.connect('clicked', self._on_send_msg)
        input_hbox.pack_start(self.btn_send, False, False, 0)

        self.btn_send_file = act_btn('Gửi File')
        self.btn_send_file.connect('clicked', self._on_send_file)
        input_hbox.pack_start(self.btn_send_file, False, False, 0)

        # Cập nhật trạng thái nút bấm ban đầu
        self._update_ui_state()

    def _update_ui_state(self):
        self.tf_cli_ip.set_sensitive(not self.connected)
        self.tf_cli_port.set_sensitive(not self.connected)
        self.tf_cli_user.set_sensitive(not self.connected)
        self.tf_msg.set_sensitive(self.connected)
        self.btn_send.set_sensitive(self.connected)
        self.btn_send_file.set_sensitive(self.connected)

        if self.connected:
            self.btn_cli.set_label('Ngắt kết nối')
        else:
            self.btn_cli.set_label('Kết nối')

        if self.server_proc:
            self.btn_srv.set_label('Dừng Server')
        else:
            self.btn_srv.set_label('Khởi chạy Server')

    def append_chat(self, text, tag_name=None):
        buf = self.chat_tv.get_buffer()
        end_iter = buf.get_end_iter()
        if tag_name:
            tag = buf.get_tag_table().lookup(tag_name)
            if not tag:
                if tag_name == 'system':
                    tag = buf.create_tag(tag_name, foreground='#ffff55', weight=700) # màu vàng
                elif tag_name == 'self':
                    tag = buf.create_tag(tag_name, foreground='#55ffff') # màu cyan
                elif tag_name == 'other':
                    tag = buf.create_tag(tag_name, foreground='#55ff55') # màu xanh lá
            buf.insert_with_tags(end_iter, text + "\n", tag)
        else:
            buf.insert(end_iter, text + "\n")
        self.chat_tv.scroll_to_iter(buf.get_end_iter(), 0.0, False, 0, 0)

    # ── Xử lý Server ─────────────────────────────────────────────────────────
    def _ensure_srv(self):
        ok, msg = ensure_compiled(SOCKET_SRV_SRC, SOCKET_SRV_BIN, "-lpthread")
        if msg: term_write(self.term, msg)
        if not ok: err(self.win, 'Biên dịch thất bại Server', msg)
        return ok

    def _toggle_server(self, _):
        if self.server_proc:
            self.server_proc.terminate()
            self.server_proc = None
            term_write(self.term, "[Hệ thống] Đã dừng Server.\n")
            self._update_ui_state()
            return

        port = self.tf_srv_port.get_text().strip()
        if not port.isdigit():
            warn(self.win, 'Vui lòng nhập Port Server hợp lệ!'); return

        term_clear(self.term)
        term_write(self.term, "[Server] Đang biên dịch Server...\n")

        if not self._ensure_srv(): return

        try:
            self.server_proc = subprocess.Popen(
                [SOCKET_SRV_BIN, port],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=SOCKET_DIR
            )

            # Đọc log đầu ra của Server
            def read_srv():
                while self.server_proc:
                    line = self.server_proc.stdout.readline()
                    if not line:
                        break
                    GLib.idle_add(term_write, self.term, f"[Server] {line}")
                GLib.idle_add(self._on_server_exit)

            threading.Thread(target=read_srv, daemon=True).start()
            term_write(self.term, f"[Hệ thống] Server đã khởi chạy trên cổng {port}.\n")
            self._update_ui_state()
        except Exception as e:
            err(self.win, 'Lỗi khởi chạy Server', str(e))

    def _on_server_exit(self):
        if self.server_proc:
            self.server_proc = None
            term_write(self.term, "[Hệ thống] Server đã dừng hoặc thoát.\n")
            self._update_ui_state()

    # ── Xử lý Client kết nối và nhận dữ liệu ───────────────────────────────
    def _toggle_client(self, _):
        if self.connected:
            self._disconnect()
            return

        ip = self.tf_cli_ip.get_text().strip()
        port_str = self.tf_cli_port.get_text().strip()
        user = self.tf_cli_user.get_text().strip()

        if not ip or not port_str.isdigit() or not user:
            warn(self.win, 'Vui lòng nhập đầy đủ IP, Port và Tên User!'); return

        port = int(port_str)
        term_write(self.term, f"[Client] Đang kết nối tới Server tại {ip}:{port}...\n")

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((ip, port))
            self.connected = True
            self._update_ui_state()

            self.append_chat(f"*** Đã kết nối tới Server {ip}:{port} ***", 'system')

            # Khởi chạy luồng nghe tin nhắn/file từ Server
            threading.Thread(target=self._client_listener, daemon=True).start()
        except Exception as e:
            err(self.win, 'Lỗi kết nối', f"Không thể kết nối: {e}")
            self.client_socket = None

    def _disconnect(self):
        if self.client_socket:
            self.connected = False
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        self.append_chat("*** Đã ngắt kết nối ***", 'system')
        self._update_ui_state()

    def _on_client_error(self, err_msg):
        term_write(self.term, f"[Client] Lỗi kết nối: {err_msg}\n")
        self._disconnect()

    def _client_listener(self):
        os.makedirs(os.path.join(SOCKET_DIR, 'received_files'), exist_ok=True)
        
        while self.connected:
            try:
                # Nhận đủ MSG_PACKET_SIZE (1400 bytes)
                data = b""
                while len(data) < MSG_PACKET_SIZE:
                    chunk = self.client_socket.recv(MSG_PACKET_SIZE - len(data))
                    if not chunk:
                        raise ConnectionError("Mất kết nối từ Server")
                    data += chunk

                packet = unpack_msg(data)
                GLib.idle_add(self._handle_packet, packet)
            except Exception as e:
                GLib.idle_add(self._on_client_error, str(e))
                break

    def _handle_packet(self, packet):
        p_type = packet['type']
        sender = packet['sender']

        if p_type == MSG_TYPE_CHAT:
            content = packet['content']
            self.append_chat(f"{sender}: {content.strip()}", 'other')
            
        elif p_type == MSG_TYPE_FILE:
            filename = packet['filename']
            filesize = packet['filesize']
            chunk_id = packet['chunk_id']
            total_chunks = packet['total_chunks']
            content = packet['content'] # byte dữ liệu thực tế

            key = (sender, filename)

            # Khởi tạo file ở chunk đầu tiên
            if chunk_id == 0:
                filepath = os.path.join(SOCKET_DIR, 'received_files', filename)
                try:
                    f = open(filepath, 'wb')
                    self.incoming_files[key] = {
                        'file': f,
                        'received': 0,
                        'total': total_chunks
                    }
                    self.append_chat(f"*** Đang nhận file '{filename}' từ {sender} ({filesize} bytes)... ***", 'system')
                except Exception as e:
                    self.append_chat(f"[Lỗi] Không thể tạo file {filename}: {e}", 'system')
                    return

            # Ghi tiếp dữ liệu chunk vào file
            if key in self.incoming_files:
                file_info = self.incoming_files[key]
                try:
                    file_info['file'].write(content)
                    file_info['received'] += 1

                    if file_info['received'] >= file_info['total']:
                        file_info['file'].close()
                        del self.incoming_files[key]
                        self.append_chat(f"*** Đã nhận xong file: '{filename}' và lưu vào thư mục received_files/ ***", 'system')
                        term_write(self.term, f"[Hệ thống] Nhận file {filename} thành công từ {sender}.\n")
                except Exception as e:
                    self.append_chat(f"[Lỗi] Lỗi khi ghi file {filename}: {e}", 'system')
                    if 'file' in file_info:
                        file_info['file'].close()
                    del self.incoming_files[key]

    # ── Gửi tin nhắn và file ──────────────────────────────────────────────────
    def _on_send_msg(self, _):
        if not self.connected or not self.client_socket:
            return

        text = self.tf_msg.get_text().strip()
        if not text:
            return

        user = self.tf_cli_user.get_text().strip()

        try:
            packet_data = pack_msg(MSG_TYPE_CHAT, user, text + "\n")
            self.client_socket.sendall(packet_data)
            
            self.append_chat(f"Tôi: {text}", 'self')
            self.tf_msg.set_text('')
        except Exception as e:
            err(self.win, 'Lỗi gửi tin nhắn', str(e))
            self._disconnect()

    def _on_send_file(self, _):
        if not self.connected or not self.client_socket:
            return

        dlg = Gtk.FileChooserDialog(title='Chọn file gửi đi', parent=self.win,
                                    action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        if dlg.run() == Gtk.ResponseType.OK:
            filepath = dlg.get_filename()
            dlg.destroy()
            # Chạy gửi file trên một luồng riêng để tránh đơ giao diện đồ họa
            threading.Thread(target=self._send_file_worker, args=(filepath,), daemon=True).start()
        else:
            dlg.destroy()

    def _send_file_worker(self, filepath):
        user = self.tf_cli_user.get_text().strip()
        filename = os.path.basename(filepath)

        try:
            with open(filepath, 'rb') as f:
                f.seek(0, 2)
                filesize = f.tell()
                f.seek(0)

                total_chunks = (filesize + FILE_CHUNK_SIZE - 1) // FILE_CHUNK_SIZE
                if total_chunks == 0:
                    total_chunks = 1

                GLib.idle_add(self.append_chat, f"*** Đang gửi file '{filename}' ({filesize} bytes, {total_chunks} chunks)... ***", 'system')

                chunk_id = 0
                while True:
                    chunk_data = f.read(FILE_CHUNK_SIZE)
                    if not chunk_data and chunk_id > 0:
                        break

                    bytes_read = len(chunk_data)
                    packet_data = pack_msg(
                        msg_type=MSG_TYPE_FILE,
                        sender=user,
                        content=chunk_data,
                        bytes_read=bytes_read,
                        filename=filename,
                        filesize=filesize,
                        chunk_id=chunk_id,
                        total_chunks=total_chunks
                    )

                    self.client_socket.sendall(packet_data)
                    chunk_id += 1
                    time.sleep(0.01) # Tránh tràn đệm socket

                    if len(chunk_data) < FILE_CHUNK_SIZE:
                        break

                GLib.idle_add(self.append_chat, f"*** Gửi file '{filename}' hoàn tất ***", 'system')
        except Exception as e:
            GLib.idle_add(err, self.win, 'Lỗi gửi file', f"Không thể gửi: {e}")
