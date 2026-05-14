APPNAME = widget-app
VERSION = 1.1.0

.PHONY: all clean install uninstall

all: install

clean:
	rm -rf dist/ rpmbuild/
	rm -f $(APPNAME)-$(VERSION).tar.gz

dist: clean
	mkdir -p dist/$(APPNAME)-$(VERSION)/manager
	mkdir -p dist/$(APPNAME)-$(VERSION)/widgets
	cp main.py widget-app.sh widget-app.desktop widget-app-autostart.desktop \
	   dist/$(APPNAME)-$(VERSION)/
	cp manager/__init__.py manager/widget_manager.py dist/$(APPNAME)-$(VERSION)/manager/
	cp widgets/__init__.py widgets/base_widget.py widgets/clock_widget.py \
	   widgets/task_widget.py widgets/weather_widget.py widgets/music_widget.py \
	   widgets/system_widget.py widgets/note_widget.py dist/$(APPNAME)-$(VERSION)/widgets/

tar: dist
	cd dist && tar czf ../$(APPNAME)-$(VERSION).tar.gz $(APPNAME)-$(VERSION)

install:
	sudo dnf install -y python3-psutil python3-requests python3-dbus python3-gobject \
	     gtk3 python3-cairo
	sudo mkdir -p /usr/share/widget-app/manager /usr/share/widget-app/widgets
	sudo cp main.py /usr/share/widget-app/
	sudo cp manager/__init__.py manager/widget_manager.py /usr/share/widget-app/manager/
	sudo cp widgets/__init__.py widgets/base_widget.py widgets/clock_widget.py \
	     widgets/task_widget.py widgets/weather_widget.py widgets/music_widget.py \
	     widgets/system_widget.py widgets/note_widget.py /usr/share/widget-app/widgets/
	sudo cp widget-app.sh /usr/bin/widget-app
	sudo chmod 0755 /usr/bin/widget-app
	sudo mkdir -p /usr/share/applications
	sudo cp widget-app.desktop /usr/share/applications/
	sudo mkdir -p /etc/xdg/autostart
	sudo cp widget-app-autostart.desktop /etc/xdg/autostart/widget-app.desktop
	@echo ""
	@echo "✓ Installed. Run 'widget-app' to start."

uninstall:
	sudo rm -rf /usr/share/widget-app
	sudo rm -f /usr/bin/widget-app
	sudo rm -f /usr/share/applications/widget-app.desktop
	sudo rm -f /etc/xdg/autostart/widget-app.desktop
	@echo "Uninstalled."
