import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
import json
import os
from datetime import datetime
from widgets.base_widget import BaseWidget
from manager.widget_manager import register_widget

TASKS_FILE = os.path.expanduser('~/.config/widget-app/tasks.json')

class TaskListWidget(BaseWidget):
    def __init__(self, on_delete=None):
        BaseWidget.__init__(self, 'task_list', 'Tasks', 300, 350, on_delete)
        self.tasks = []
        self._load_tasks()
        self._build_content()

    def _build_content(self):
        css = """
            .task-entry {
                background-color: rgba(255, 255, 255, 0.06);
                color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 13px;
            }
            .task-entry:focus {
                border: 1px solid rgba(100, 181, 246, 0.4);
            }
            .task-item {
                background-color: rgba(255, 255, 255, 0.04);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.04);
                padding: 8px 12px;
                margin: 3px 0;
            }
            .task-text {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
            }
            .task-text-done {
                color: rgba(255, 255, 255, 0.3);
                font-size: 13px;
            }
            .task-time {
                color: rgba(255, 255, 255, 0.25);
                font-size: 10px;
            }
            .task-count {
                color: rgba(255, 255, 255, 0.4);
                font-size: 11px;
                padding: 4px 0;
            }
            .add-task-btn {
                background-color: rgba(100, 181, 246, 0.12);
                color: #64b5f6;
                border: 1px solid rgba(100, 181, 246, 0.2);
                border-radius: 10px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
                min-width: 80px;
            }
            .add-task-btn:hover {
                background-color: rgba(100, 181, 246, 0.2);
            }
            .task-checkbox {
                color: rgba(129, 199, 132, 0.8);
            }
            .delete-task-btn {
                background: none;
                border: none;
                color: rgba(255, 255, 255, 0.25);
                font-size: 14px;
                padding: 0 4px;
            }
            .delete-task-btn:hover {
                color: #ef5350;
            }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.entry = Gtk.Entry()
        self.entry.get_style_context().add_class('task-entry')
        self.entry.set_placeholder_text('Add a new task...')
        self.entry.set_can_focus(True)
        self.entry.connect('activate', self._on_add_task)

        add_btn = Gtk.Button(label='+ Add')
        add_btn.get_style_context().add_class('add-task-btn')
        add_btn.connect('clicked', self._on_add_task)

        input_box.pack_start(self.entry, True, True, 0)
        input_box.pack_end(add_btn, False, False, 0)
        self.content.pack_start(input_box, False, False, 0)

        self.count_label = Gtk.Label()
        self.count_label.get_style_context().add_class('task-count')
        self.count_label.set_xalign(0.0)
        self.content.pack_start(self.count_label, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.task_list = Gtk.ListBox()
        self.task_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.add(self.task_list)
        self.content.pack_start(scroll, True, True, 0)

        self._rebuild_list()
        GLib.timeout_add(200, self.entry.grab_focus)

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

    def _rebuild_list(self):
        for child in self.task_list.get_children():
            self.task_list.remove(child)

        done_count = sum(1 for t in self.tasks if t['done'])
        total = len(self.tasks)
        self.count_label.set_text(f'{total - done_count} remaining  ·  {total} total')

        for i, task in enumerate(self.tasks):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.get_style_context().add_class('task-item')

            cb = Gtk.CheckButton()
            cb.set_active(task['done'])
            cb.get_style_context().add_class('task-checkbox')
            cb.connect('toggled', self._on_toggle_task, i)

            text_lbl = Gtk.Label(label=task['text'])
            text_lbl.set_xalign(0.0)
            text_lbl.set_line_wrap(True)
            if task['done']:
                text_lbl.get_style_context().add_class('task-text-done')
            else:
                text_lbl.get_style_context().add_class('task-text')

            del_btn = Gtk.Button(label='✕')
            del_btn.get_style_context().add_class('delete-task-btn')
            del_btn.set_size_request(24, 24)
            del_btn.connect('clicked', self._on_delete_task, i)

            row.pack_start(cb, False, False, 0)
            row.pack_start(text_lbl, True, True, 0)
            row.pack_end(del_btn, False, False, 0)

            self.task_list.add(row)

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
                except:
                    self.tasks = []

    def _save_tasks(self):
        with open(TASKS_FILE, 'w') as f:
            json.dump(self.tasks, f, indent=2)

    def refresh(self):
        pass

register_widget('task_list', 'Task List', TaskListWidget, '✓')
