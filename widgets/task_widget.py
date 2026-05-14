"""
Task List Widget
- Full keyboard input works on Wayland (via XWayland / GDK_BACKEND=x11)
- Clicking anywhere on the entry field focuses it immediately
- Press Enter to add; ✕ to delete; checkbox to toggle done
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import json
import os
from datetime import datetime
from widgets.base_widget import BaseWidget
from manager.widget_manager import register_widget

TASKS_FILE = os.path.expanduser('~/.config/widget-app/tasks.json')

TASK_CSS = """
    .task-entry {
        background-color: rgba(255, 255, 255, 0.09);
        color: rgba(255, 255, 255, 0.92);
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 12px;
        padding: 8px 12px;
        font-size: 13px;
        caret-color: #64b5f6;
    }
    .task-entry:focus {
        border: 1px solid rgba(100, 181, 246, 0.55);
        background-color: rgba(255, 255, 255, 0.12);
    }
    .task-item {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 6px 10px;
        margin: 2px 0;
    }
    .task-text {
        color: rgba(255, 255, 255, 0.90);
        font-size: 13px;
    }
    .task-text-done {
        color: rgba(255, 255, 255, 0.32);
        font-size: 13px;
    }
    .task-count {
        color: rgba(255, 255, 255, 0.38);
        font-size: 10px;
        padding: 2px 0;
    }
    .add-task-btn {
        background-color: rgba(100, 181, 246, 0.16);
        color: #64b5f6;
        border: 1px solid rgba(100, 181, 246, 0.28);
        border-radius: 10px;
        padding: 5px 12px;
        font-size: 12px;
        font-weight: 700;
        min-width: 64px;
    }
    .add-task-btn:hover {
        background-color: rgba(100, 181, 246, 0.28);
        color: #bbdefb;
    }
    .delete-task-btn {
        background: none;
        border: none;
        color: rgba(255, 255, 255, 0.22);
        font-size: 13px;
        padding: 0 4px;
        min-width: 22px;
    }
    .delete-task-btn:hover {
        color: #ff453a;
    }
    .clear-done-btn {
        background: none;
        border: none;
        color: rgba(255, 69, 58, 0.55);
        font-size: 10px;
        padding: 0 4px;
        font-weight: 600;
    }
    .clear-done-btn:hover {
        color: #ff453a;
    }
    /* Checkbox override – keep it visible on dark bg */
    check {
        border: 1px solid rgba(255, 255, 255, 0.30);
        background-color: rgba(255, 255, 255, 0.06);
        border-radius: 4px;
    }
    check:checked {
        background-color: rgba(48, 209, 88, 0.70);
        border: 1px solid rgba(48, 209, 88, 0.80);
    }
"""


class TaskListWidget(BaseWidget):
    def __init__(self, on_delete=None):
        BaseWidget.__init__(self, 'task_list', 'Tasks', 300, 360, on_delete)
        self.tasks = []
        self._load_tasks()
        self._apply_task_css()
        self._build_content()

    def _apply_task_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(TASK_CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_content(self):
        # ── Input row ──
        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        input_box.set_margin_top(6)
        input_box.set_margin_bottom(4)

        self.entry = Gtk.Entry()
        self.entry.get_style_context().add_class('task-entry')
        self.entry.set_placeholder_text('New task…')
        # Critical: allow focus so the entry actually receives key events
        self.entry.set_can_focus(True)
        self.entry.set_focus_on_click(True)
        self.entry.connect('activate', self._on_add_task)

        add_btn = Gtk.Button(label='＋ Add')
        add_btn.get_style_context().add_class('add-task-btn')
        add_btn.connect('clicked', self._on_add_task)
        # Prevent button from stealing focus away from entry
        add_btn.set_focus_on_click(False)

        input_box.pack_start(self.entry, True, True, 0)
        input_box.pack_end(add_btn, False, False, 0)
        self.content.pack_start(input_box, False, False, 0)

        # ── Counter row ──
        counter_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.count_label = Gtk.Label()
        self.count_label.get_style_context().add_class('task-count')
        self.count_label.set_xalign(0.0)
        counter_row.pack_start(self.count_label, True, True, 0)

        clear_btn = Gtk.Button(label='Clear done')
        clear_btn.get_style_context().add_class('clear-done-btn')
        clear_btn.set_relief(Gtk.ReliefStyle.NONE)
        clear_btn.set_focus_on_click(False)
        clear_btn.connect('clicked', self._on_clear_done)
        counter_row.pack_end(clear_btn, False, False, 0)

        self.content.pack_start(counter_row, False, False, 0)

        # ── Task list ──
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.task_list = Gtk.ListBox()
        self.task_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.add(self.task_list)
        self.content.pack_start(scroll, True, True, 0)

        self._rebuild_list()

        # Grab focus slightly deferred so window is ready
        GLib.timeout_add(100, self._grab_entry_focus)

    def _grab_entry_focus(self):
        """Grab keyboard focus for the entry field."""
        self.present()          # Ensure window has WM focus
        self.entry.grab_focus()
        return False            # Don't repeat

    # ── Task actions ──────────────────────────────────────────────────────────

    def _on_add_task(self, widget):
        text = self.entry.get_text().strip()
        if text:
            self.tasks.append({
                'text': text,
                'done': False,
                'created': datetime.now().isoformat()
            })
            self.entry.set_text('')
            self._save_tasks()
            self._rebuild_list()
        self.entry.grab_focus()

    def _on_clear_done(self, btn):
        self.tasks = [t for t in self.tasks if not t['done']]
        self._save_tasks()
        self._rebuild_list()

    def _rebuild_list(self):
        for child in self.task_list.get_children():
            self.task_list.remove(child)

        done_count = sum(1 for t in self.tasks if t['done'])
        total = len(self.tasks)
        remaining = total - done_count
        self.count_label.set_text(
            f'{remaining} remaining · {total} total'
        )

        for i, task in enumerate(self.tasks):
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row_box.get_style_context().add_class('task-item')

            cb = Gtk.CheckButton()
            cb.set_active(task['done'])
            cb.set_focus_on_click(False)
            cb.connect('toggled', self._on_toggle_task, i)

            text_lbl = Gtk.Label(label=task['text'])
            text_lbl.set_xalign(0.0)
            text_lbl.set_line_wrap(True)
            text_lbl.set_max_width_chars(28)
            css_class = 'task-text-done' if task['done'] else 'task-text'
            text_lbl.get_style_context().add_class(css_class)

            del_btn = Gtk.Button(label='✕')
            del_btn.get_style_context().add_class('delete-task-btn')
            del_btn.set_size_request(22, 22)
            del_btn.set_focus_on_click(False)
            del_btn.connect('clicked', self._on_delete_task, i)

            row_box.pack_start(cb, False, False, 0)
            row_box.pack_start(text_lbl, True, True, 0)
            row_box.pack_end(del_btn, False, False, 0)

            self.task_list.add(row_box)

        self.task_list.show_all()

    def _on_toggle_task(self, cb, index):
        if 0 <= index < len(self.tasks):
            self.tasks[index]['done'] = cb.get_active()
            self._save_tasks()
            self._rebuild_list()

    def _on_delete_task(self, btn, index):
        if 0 <= index < len(self.tasks):
            del self.tasks[index]
            self._save_tasks()
            self._rebuild_list()

    def _load_tasks(self):
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE) as f:
                try:
                    self.tasks = json.load(f)
                except Exception:
                    self.tasks = []

    def _save_tasks(self):
        with open(TASKS_FILE, 'w') as f:
            json.dump(self.tasks, f, indent=2)

    def refresh(self):
        pass


register_widget('task_list', 'Task List', TaskListWidget, '✓')
