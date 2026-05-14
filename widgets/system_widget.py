import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import psutil
from datetime import datetime
from widgets.base_widget import BaseWidget
from manager.widget_manager import register_widget

SYS_CSS = """
    .sys-title {
        color: rgba(100, 181, 246, 0.85);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .sys-value {
        color: rgba(255, 255, 255, 0.92);
        font-size: 18px;
        font-weight: 600;
    }
    .sys-unit {
        color: rgba(255, 255, 255, 0.35);
        font-size: 11px;
    }
    .sys-card {
        background-color: rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.07);
        padding: 10px;
        margin: 2px;
    }
"""


class SystemMonitorWidget(BaseWidget):
    def __init__(self, on_delete=None):
        BaseWidget.__init__(self, 'system_monitor', 'System', 260, 300, on_delete)
        self._apply_sys_css()
        self._build_content()
        self._update_stats()

    def _apply_sys_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(SYS_CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_content(self):
        grid = Gtk.Grid()
        grid.set_column_spacing(6)
        grid.set_row_spacing(6)
        grid.set_margin_top(6)
        self.content.pack_start(grid, True, True, 0)

        self.cpu_card  = self._make_card(grid, 'CPU',  0, 0)
        self.mem_card  = self._make_card(grid, 'MEM',  1, 0)
        self.disk_card = self._make_card(grid, 'DISK', 0, 1)
        self.proc_card = self._make_card(grid, 'PROC', 1, 1)

        # Uptime spanning both columns
        up_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        up_box.get_style_context().add_class('sys-card')
        up_lbl = Gtk.Label(label='UPTIME')
        up_lbl.get_style_context().add_class('sys-title')
        up_lbl.set_xalign(0.0)
        self.uptime_value = Gtk.Label(label='--')
        self.uptime_value.get_style_context().add_class('sys-value')
        self.uptime_value.set_xalign(0.0)
        up_box.pack_start(up_lbl, False, False, 0)
        up_box.pack_start(self.uptime_value, False, False, 0)
        grid.attach(up_box, 0, 2, 2, 1)

    def _make_card(self, grid, label, col, row):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.get_style_context().add_class('sys-card')

        lbl = Gtk.Label(label=label)
        lbl.get_style_context().add_class('sys-title')
        lbl.set_xalign(0.0)

        val_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        val = Gtk.Label(label='--')
        val.get_style_context().add_class('sys-value')
        unit = Gtk.Label(label='')
        unit.get_style_context().add_class('sys-unit')
        val_box.pack_start(val, False, False, 0)
        val_box.pack_start(unit, False, False, 0)

        box.pack_start(lbl, False, False, 0)
        box.pack_start(val_box, False, False, 0)
        grid.attach(box, col, row, 1, 1)
        return {'val': val, 'unit': unit}

    def _update_stats(self):
        cpu_pct = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        procs = len(psutil.pids())

        self.cpu_card['val'].set_text(f'{cpu_pct:.0f}')
        self.cpu_card['unit'].set_text('%')

        mem_gb = mem.used / (1024**3)
        mem_total = mem.total / (1024**3)
        self.mem_card['val'].set_text(f'{mem_gb:.1f}')
        self.mem_card['unit'].set_text(f'/{mem_total:.0f}GB')

        disk_gb = disk.used / (1024**3)
        disk_total = disk.total / (1024**3)
        self.disk_card['val'].set_text(f'{disk_gb:.0f}')
        self.disk_card['unit'].set_text(f'/{disk_total:.0f}GB')

        self.proc_card['val'].set_text(f'{procs}')
        self.proc_card['unit'].set_text('proc')

        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        days = uptime.days
        hours = uptime.seconds // 3600
        mins = (uptime.seconds % 3600) // 60
        self.uptime_value.set_text(f'{days}d {hours}h {mins}m' if days else f'{hours}h {mins}m')
        return True

    def refresh(self):
        self._update_stats()


register_widget('system_monitor', 'System Monitor', SystemMonitorWidget, '⚙')
