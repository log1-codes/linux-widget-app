#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Widget App Installer ==="
echo ""
echo "Choose installation method:"
echo "  1) Quick install (system packages via sudo)"
echo "  2) Build RPM package (requires rpmbuild)"
echo "  3) Run from source (no install, just launch)"
echo ""
read -rp "Choice [1-3]: " choice

case "$choice" in
    1)
        echo "Installing system dependencies..."
        sudo dnf install -y python3-psutil python3-requests python3-dbus \
                            python3-gobject gtk3
        echo "Copying files..."
        sudo mkdir -p /usr/share/widget-app/manager /usr/share/widget-app/widgets
        sudo cp "$DIR"/main.py /usr/share/widget-app/
        sudo cp "$DIR"/manager/*.py /usr/share/widget-app/manager/
        sudo cp "$DIR"/widgets/*.py /usr/share/widget-app/widgets/
        sudo bash -c 'cat > /usr/bin/widget-app << "EOF"
#!/bin/sh
exec /usr/bin/python3 /usr/share/widget-app/main.py "$@"
EOF'
        sudo chmod 0755 /usr/bin/widget-app
        echo ""
        echo "Installation complete! Run 'widget-app' to start."
        ;;
    2)
        echo "Building RPM..."
        cd "$DIR" && make rpm
        echo ""
        echo "RPM built. Install with:"
        echo "  sudo dnf install ./widget-app-*.rpm"
        ;;
    3)
        echo "Launching from source..."
        echo "  Run: python3 \"$DIR/main.py\""
        echo "  Or:  $DIR/run.sh"
        ;;
    *)
        echo "Invalid choice." >&2
        exit 1
        ;;
esac
