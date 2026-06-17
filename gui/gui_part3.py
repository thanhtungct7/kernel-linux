#!/usr/bin/python3
"""Part 3 – Kernel module: test.c (insmod với module_param)"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import random

from gui.gui_common import (
    DIR3,
    run_bg, run_cmd,
    title_lbl, act_btn, make_term,
    term_write, term_clear,
    warn,
)


class KernelModulePanel(Gtk.Box):
    OPS = [
        ('1', 'Giai thừa  (factorial)'),
        ('2', 'Cộng ma trận  (matadd)'),
        ('3', 'Nhân ma trận  (matmul)'),
        ('4', 'Số nguyên tố trong khoảng'),
        ('5', 'Đếm số nhỏ hơn s trong ma trận'),
        ('6', 'Đếm số chia hết cho s'),
        ('7', 'Đếm số nguyên tố trong ma trận'),
    ]

    def __init__(self, win):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.win = win
        self._spin       = {}
        self._cells      = {}
        self._mat_meta   = {}
        self._rand_range = {}

        self.pack_start(title_lbl('Module Kernel – Toán học  [test.c]'), False, False, 0)

        # ── Frame 1: Biên dịch ────────────────────────────────────────────
        fr1 = Gtk.Frame(label='  Biên dịch  ')
        fr1.set_margin_start(8); fr1.set_margin_end(8)
        box1 = Gtk.Box(spacing=8,
                       margin_start=10, margin_end=10,
                       margin_top=8,    margin_bottom=8)
        for lbl2, cb in [('Build  (make)', self._build),
                         ('Clean',         self._clean)]:
            b = act_btn(lbl2); b.connect('clicked', cb)
            box1.pack_start(b, False, False, 0)
        fr1.add(box1)
        self.pack_start(fr1, False, False, 0)

        # ── Frame 2: Tham số & Tính toán ──────────────────────────────────
        fr2 = Gtk.Frame(label='  Tham so & Tinh toan  ')
        fr2.set_margin_start(8); fr2.set_margin_end(8)
        box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6,
                       margin_start=10, margin_end=10,
                       margin_top=8,    margin_bottom=8)

        op_row = Gtk.Box(spacing=8)
        lbl_op = Gtk.Label(label='Phep tinh:')
        lbl_op.get_style_context().add_class('kern-lbl')
        op_row.pack_start(lbl_op, False, False, 0)
        self.combo = Gtk.ComboBoxText()
        self.combo.get_style_context().add_class('kern-combo')
        for code, name in self.OPS:
            self.combo.append_text(f'{code}. {name}')
        self.combo.set_active(0)
        self.combo.connect('changed', lambda _: self._rebuild_all())
        op_row.pack_start(self.combo, True, True, 0)
        box2.pack_start(op_row, False, False, 0)

        self._input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        sw_in = Gtk.ScrolledWindow()
        sw_in.set_hexpand(True)
        sw_in.set_vexpand(True)
        sw_in.set_min_content_height(360)
        sw_in.set_max_content_height(600)
        sw_in.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw_in.add(self._input_box)
        box2.pack_start(sw_in, True, True, 0)

        b_run = act_btn('Chay  (sudo insmod)')
        b_run.connect('clicked', self._run)
        box2.pack_start(b_run, False, False, 0)

        fr2.add(box2)
        self.pack_start(fr2, True, True, 0)

        # ── Frame 3: Kết quả ──────────────────────────────────────────────
        fr3 = Gtk.Frame(label='  Ket qua  ')
        fr3.set_margin_start(8); fr3.set_margin_end(8)
        box3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4,
                       margin_start=10, margin_end=10,
                       margin_top=8,    margin_bottom=8)
        b_dmesg = act_btn('Xem ket qua  (dmesg)')
        b_dmesg.connect('clicked', self._dmesg)
        box3.pack_start(b_dmesg, False, False, 0)
        self.term, sw_term = make_term()
        box3.pack_start(sw_term, True, True, 0)
        fr3.add(box3)
        self.pack_start(fr3, True, True, 0)

        self._rebuild_all()

    # ── helpers ────────────────────────────────────────────────────────────

    def _sv(self, key, default=2):
        sb = self._spin.get(key)
        return int(sb.get_value()) if sb else default

    def _make_spinbutton(self, key, lo, hi, default):
        adj = Gtk.Adjustment(value=default, lower=lo, upper=hi,
                             step_increment=1, page_increment=5)
        sb = Gtk.SpinButton(adjustment=adj, numeric=True)
        sb.set_width_chars(5)
        sb.get_style_context().add_class('kern-spin')
        self._spin[key] = sb
        return sb

    def _scalar_row(self, specs):
        row = Gtk.Box(spacing=14)
        for key, lbl2, lo, hi, default in specs:
            lbl_w = Gtk.Label(label=lbl2)
            lbl_w.get_style_context().add_class('kern-lbl')
            row.pack_start(lbl_w, False, False, 0)
            row.pack_start(self._make_spinbutton(key, lo, hi, default),
                           False, False, 0)
        self._input_box.pack_start(row, False, False, 0)

    def _matrix_section(self, mat_key, title, row_key, col_key):
        frame = Gtk.Frame(label=f'  {title}  ')
        frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        lbl_w = frame.get_label_widget()
        if lbl_w:
            lbl_w.get_style_context().add_class('kern-frame-lbl')

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                        margin_start=6, margin_end=6,
                        margin_top=4, margin_bottom=6)
        frame.add(outer)

        btn_row = Gtk.Box(spacing=6, margin_bottom=4)
        b_rand = act_btn('Ngẫu nhiên')
        b_rand.connect('clicked', lambda _: self._randomize(mat_key))
        btn_row.pack_start(b_rand, False, False, 0)

        lbl_tu = Gtk.Label(label='từ')
        lbl_tu.get_style_context().add_class('kern-lbl')
        btn_row.pack_start(lbl_tu, False, False, 0)
        sp_lo = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(value=-9, lower=-9999, upper=9999,
                                      step_increment=1, page_increment=10),
            numeric=True)
        sp_lo.set_width_chars(5)
        sp_lo.get_style_context().add_class('kern-spin')
        btn_row.pack_start(sp_lo, False, False, 0)

        lbl_den = Gtk.Label(label='đến')
        lbl_den.get_style_context().add_class('kern-lbl')
        btn_row.pack_start(lbl_den, False, False, 0)
        sp_hi = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(value=9, lower=-9999, upper=9999,
                                      step_increment=1, page_increment=10),
            numeric=True)
        sp_hi.set_width_chars(5)
        sp_hi.get_style_context().add_class('kern-spin')
        btn_row.pack_start(sp_hi, False, False, 0)

        outer.pack_start(btn_row, False, False, 0)

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.pack_start(container, False, False, 0)

        self._mat_meta[mat_key] = (container, row_key, col_key)
        self._rand_range[mat_key] = (sp_lo, sp_hi)

        self._input_box.pack_start(frame, False, False, 0)
        self._fill_matrix(mat_key)

    def _fill_matrix(self, mat_key):
        container, row_key, col_key = self._mat_meta[mat_key]
        for ch in list(container.get_children()):
            container.remove(ch)

        rows = min(max(1, self._sv(row_key, 2)), 10)
        cols = min(max(1, self._sv(col_key, 2)), 10)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3,
                       margin_start=4, margin_end=4,
                       margin_top=4, margin_bottom=4)
        cells = []
        for i in range(rows):
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
            row_cells = []
            for j in range(cols):
                e = Gtk.Entry()
                e.set_text('0')
                e.set_width_chars(4)
                e.set_max_width_chars(6)
                e.set_alignment(0.5)
                e.get_style_context().add_class('kern-cell')
                e.connect('key-press-event', self._cell_key, i, j, mat_key)
                hbox.pack_start(e, False, False, 0)
                row_cells.append(e)
            vbox.pack_start(hbox, False, False, 0)
            cells.append(row_cells)

        self._cells[mat_key] = cells
        container.pack_start(vbox, False, False, 0)
        container.show_all()
        container.queue_resize()

    def _cell_key(self, entry, event, row_i, col_i, mat_key):
        cells = self._cells.get(mat_key, [])
        n_rows = len(cells)
        n_cols = len(cells[row_i]) if cells else 0

        if (event.keyval == Gdk.KEY_v and
                event.state & Gdk.ModifierType.CONTROL_MASK):
            clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            text = clip.wait_for_text() or ''
            lines = [l for l in text.splitlines() if l.strip()]
            if len(lines) > 1 or (lines and '\t' in lines[0]):
                for ri, line in enumerate(lines):
                    tr = row_i + ri
                    if tr >= n_rows:
                        break
                    if '\t' in line:
                        vals = line.split('\t')
                    elif ',' in line:
                        vals = line.split(',')
                    else:
                        vals = line.split()
                    for ci, val in enumerate(vals):
                        tc = col_i + ci
                        if tc >= len(cells[tr]):
                            break
                        cells[tr][tc].set_text(val.strip())
                return True

        if event.keyval == Gdk.KEY_Tab:
            if col_i + 1 < n_cols:
                cells[row_i][col_i + 1].grab_focus()
            elif row_i + 1 < n_rows:
                cells[row_i + 1][0].grab_focus()
            return True

        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if row_i + 1 < n_rows:
                tc = min(col_i, len(cells[row_i + 1]) - 1)
                cells[row_i + 1][tc].grab_focus()
            return True

        return False

    def _on_dim_changed(self, *_):
        for mk in list(self._mat_meta):
            self._fill_matrix(mk)

    def _randomize(self, mat_key):
        sp_lo, sp_hi = self._rand_range.get(mat_key, (None, None))
        lo = int(sp_lo.get_value()) if sp_lo else -9
        hi = int(sp_hi.get_value()) if sp_hi else  9
        if lo > hi:
            lo, hi = hi, lo
        for row in self._cells.get(mat_key, []):
            for e in row:
                e.set_text(str(random.randint(lo, hi)))

    def _connect_dim(self, keys):
        for k in keys:
            if k in self._spin:
                self._spin[k].connect('value-changed', self._on_dim_changed)

    def _rebuild_all(self):
        saved = {k: int(s.get_value()) for k, s in self._spin.items()}

        for ch in self._input_box.get_children():
            self._input_box.remove(ch)
        self._spin.clear(); self._cells.clear()
        self._mat_meta.clear(); self._rand_range.clear()

        idx = self.combo.get_active()
        if idx < 0:
            return
        code = self.OPS[idx][0]

        def sv(k, fb): return saved.get(k, fb)

        if code == '1':
            self._scalar_row([('d', 'Số n  (d):', 0, 1000, sv('d', 5))])

        elif code == '2':
            self._scalar_row([
                ('p', 'Số hàng  (p):', 1, 10, sv('p', 2)),
                ('q', 'Số cột   (q):', 1, 10, sv('q', 2)),
            ])
            self._connect_dim(['p', 'q'])
            self._matrix_section('a', 'Ma trận A', 'p', 'q')
            self._matrix_section('b', 'Ma trận B', 'p', 'q')

        elif code == '3':
            self._scalar_row([
                ('p', 'Hàng A  (p):', 1, 10, sv('p', 2)),
                ('q', 'Cột A = Hàng B  (q):', 1, 10, sv('q', 2)),
                ('s', 'Cột B  (s):', 1, 10, sv('s', 2)),
            ])
            self._connect_dim(['p', 'q', 's'])
            self._matrix_section('a', 'Ma trận A  (p × q)', 'p', 'q')
            self._matrix_section('b', 'Ma trận B  (q × s)', 'q', 's')

        elif code == '4':
            self._scalar_row([
                ('p', 'Từ  (p):', 0, 9999, sv('p', 1)),
                ('s', 'Đến (s):', 0, 9999, sv('s', 20)),
            ])

        elif code == '5':
            self._scalar_row([
                ('p', 'Số hàng  (p):', 1, 10, sv('p', 2)),
                ('q', 'Số cột   (q):', 1, 10, sv('q', 2)),
                ('s', 'Nhỏ hơn (s):', -9999, 9999, sv('s', 5)),
            ])
            self._connect_dim(['p', 'q'])
            self._matrix_section('a', 'Ma trận A', 'p', 'q')

        elif code == '6':
            self._scalar_row([
                ('p', 'Số hàng  (p):', 1, 10, sv('p', 2)),
                ('q', 'Số cột   (q):', 1, 10, sv('q', 2)),
                ('s', 'Chia hết cho (s):', 1, 9999, sv('s', 3)),
            ])
            self._connect_dim(['p', 'q'])
            self._matrix_section('a', 'Ma trận A', 'p', 'q')

        elif code == '7':
            self._scalar_row([
                ('p', 'Số hàng  (p):', 1, 10, sv('p', 2)),
                ('q', 'Số cột   (q):', 1, 10, sv('q', 2)),
            ])
            self._connect_dim(['p', 'q'])
            self._matrix_section('a', 'Ma trận A', 'p', 'q')

        self._input_box.show_all()

    # ── actions ────────────────────────────────────────────────────────────

    def _cb(self, o, e, rc):
        term_write(self.term, (o or '') + (e or ''))

    def _build(self, _):
        term_write(self.term, '$ make  [part3]\n')
        run_bg('make', cwd=DIR3, callback=self._cb)

    def _clean(self, _):
        run_bg('make clean', cwd=DIR3, callback=self._cb)

    def _run(self, _):
        idx = self.combo.get_active()
        if idx < 0: return
        code = self.OPS[idx][0]
        args = [f'choice={code}']

        for key, sb in self._spin.items():
            args.append(f'{key}={int(sb.get_value())}')

        for mat_key, rows_list in self._cells.items():
            flat = []
            for row_cells in rows_list:
                for e in row_cells:
                    val = e.get_text().strip() or '0'
                    try:
                        int(val)
                    except ValueError:
                        warn(self.win, f'Ô [{mat_key}] chứa giá trị không hợp lệ: "{val}"')
                        return
                    flat.append(val)
            args.append(f'{mat_key}={",".join(flat)}')

        cmd = f'sudo rmmod test 2>/dev/null; sudo insmod test.ko {" ".join(args)}'
        term_write(self.term, f'$ {cmd}\n')
        run_bg(cmd, cwd=DIR3, callback=self._cb)

    def _dmesg(self, _):
        o, e, _ = run_cmd('sudo dmesg | tail -40')
        term_clear(self.term)
        term_write(self.term, o or e)
