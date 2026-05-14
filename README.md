# Widget App

Desktop widgets for Linux — analog clock, task list, weather, music now-playing, system monitor, and quick notes. All widgets are draggable, resizable, and persist their positions across sessions.

![Widget Manager](https://img.shields.io/badge/GTK3-PyGObject-blue) ![Python](https://img.shields.io/badge/python-3.8+-brightgreen) ![License](https://img.shields.io/badge/license-MIT-green)

## Widgets

| Widget | Description |
|--------|-------------|
| 🕐 Analog Clock | Smooth analog hands + digital time + date |
| ✓ Task List | Todo list with checkboxes, add/delete/clear done |
| 🌤 Weather | Current temp, feels-like, humidity, wind (Open-Meteo) |
| 🎵 Now Playing | MPRIS integration — Spotify, VLC, mpv, Firefox, etc. |
| ⚙ System Monitor | CPU, RAM, disk, process count, uptime |
| 📝 Quick Note | Sticky note with auto-save |

## Prerequisites

- **Python 3.8+**
- **GTK3** runtime libraries
- **PyGObject** — Python GTK3 bindings
- A **Wayland** compositor (GNOME/KDE) or **X11** session

### Install system dependencies

**Fedora / RHEL / CentOS:**
```bash
sudo dnf install -y python3-gobject python3-psutil python3-requests python3-dbus gtk3 python3-cairo
```

**Ubuntu / Debian:**
```bash
sudo apt install -y python3-gi python3-gi-cairo python3-psutil python3-requests python3-dbus gir1.2-gtk-3.0
```

**Arch Linux:**
```bash
sudo pacman -S python-gobject python-psutil python-requests python-dbus gtk3
```

**openSUSE:**
```bash
sudo zypper install python3-gobject python3-psutil python3-requests python3-dbus gtk3
```

## Installation

### Option 1: Run from source (no install, any distro)

```bash
git clone https://github.com/log1-codes/linux-widget-app.git
cd widget-app
./run.sh
```

Or manually:
```bash
python3 main.py
```

### Option 2: Quick install (Fedora)

Run the interactive installer:
```bash
./install.sh
```

Or use the Makefile directly:
```bash
make install
```

This copies files to `/usr/share/widget-app/`, creates a `/usr/bin/widget-app` launcher, installs the `.desktop` file, and enables autostart.

### Option 3: Build an RPM (Fedora/RHEL)

```bash
make rpm
# or
./install.sh  # then choose option 2
```

Then install the resulting RPM:
```bash
sudo dnf install ./widget-app-*.rpm
```

### Option 4: Manual install (any distro)

```bash
# Copy sources
sudo mkdir -p /usr/share/widget-app/manager /usr/share/widget-app/widgets
sudo cp main.py /usr/share/widget-app/
sudo cp manager/*.py /usr/share/widget-app/manager/
sudo cp widgets/*.py /usr/share/widget-app/widgets/

# Create launcher
sudo bash -c 'cat > /usr/bin/widget-app << "EOF"
#!/bin/sh
export GDK_BACKEND=x11
exec /usr/bin/python3 /usr/share/widget-app/main.py "$@"
EOF'
sudo chmod 0755 /usr/bin/widget-app

# Optional: desktop entry & autostart
sudo mkdir -p /usr/share/applications
sudo cp widget-app.desktop /usr/share/applications/
sudo mkdir -p /etc/xdg/autostart
sudo cp widget-app-autostart.desktop /etc/xdg/autostart/widget-app.desktop
```

## Usage

- Run `widget-app` (installed) or `./run.sh` (source)
- A tray icon appears in the system tray — click it to **toggle the Widget Manager**
- In the manager, click **+ Add** to place widgets on your desktop
- **Drag** widgets by their title bar
- **Resize** widgets by the bottom-right corner
- Close widgets with the **×** button or **Escape** key
- Right-click the tray icon → **Quit** to exit

Widgets and task lists persist automatically.

## Wayland notes

This app forces `GDK_BACKEND=x11` (XWayland) automatically when run on Wayland. This is required because:
1. GTK window `DOCK`/`KEEP_BELOW` hints behave correctly under XWayland
2. Keyboard input is delivered to task/note widgets (Wayland security model blocks it otherwise)

No manual configuration is needed — `run.sh` and the installed `widget-app` launcher handle this.

## Uninstall

**If installed via Makefile or install.sh:**
```bash
make uninstall
```

**Manual:**
```bash
sudo rm -rf /usr/share/widget-app
sudo rm -f /usr/bin/widget-app
sudo rm -f /usr/share/applications/widget-app.desktop
sudo rm -f /etc/xdg/autostart/widget-app.desktop
```

Remove config data (optional):
```bash
rm -rf ~/.config/widget-app
```
## Made with 💖 by Anurag Singh

[Check My Work Here ](https://www.anurag.engineer)
## License

MIT
