APPNAME = widget-app
VERSION = 1.0.0

.PHONY: all clean tar rpm install uninstall

all: rpm

clean:
	rm -rf dist/
	rm -f $(APPNAME)-$(VERSION).tar.gz
	rm -f widget-app.sh

dist: clean widget-app.sh
	mkdir -p dist/$(APPNAME)-$(VERSION)/manager
	mkdir -p dist/$(APPNAME)-$(VERSION)/widgets
	cp main.py dist/$(APPNAME)-$(VERSION)/
	cp widget-app.sh dist/$(APPNAME)-$(VERSION)/
	cp widget-app.desktop dist/$(APPNAME)-$(VERSION)/
	cp widget-app-autostart.desktop dist/$(APPNAME)-$(VERSION)/
	cp manager/__init__.py manager/widget_manager.py dist/$(APPNAME)-$(VERSION)/manager/
	cp widgets/__init__.py widgets/base_widget.py widgets/clock_widget.py \
	   widgets/task_widget.py widgets/weather_widget.py widgets/music_widget.py \
	   widgets/system_widget.py widgets/note_widget.py dist/$(APPNAME)-$(VERSION)/widgets/

tar: dist
	cd dist && tar czf ../$(APPNAME)-$(VERSION).tar.gz $(APPNAME)-$(VERSION)

rpm: tar
	rpmbuild -tb $(APPNAME)-$(VERSION).tar.gz || \
	rpmbuild -tb --define "_specdir $(PWD)" --define "_sourcedir $(PWD)" \
	        --define "_builddir $(PWD)/rpmbuild" --define "_srcrpmdir $(PWD)" \
	        --define "_rpmdir $(PWD)" $(APPNAME)-$(VERSION).tar.gz

widget-app.sh:
	printf '#!/bin/sh\nif [ "$$XDG_SESSION_TYPE" = "wayland" ] && [ -z "$$GDK_BACKEND" ]; then\n\texport GDK_BACKEND=x11\nfi\nexec /usr/bin/python3 /usr/share/widget-app/main.py "$$@"\n' > widget-app.sh
	chmod 0755 widget-app.sh

install: widget-app.sh
	sudo dnf install -y python3-psutil python3-requests python3-dbus python3-gobject gtk3
	sudo mkdir -p /usr/share/widget-app/manager /usr/share/widget-app/widgets
	sudo cp main.py /usr/share/widget-app/
	sudo cp manager/__init__.py manager/widget_manager.py /usr/share/widget-app/manager/
	sudo cp widgets/__init__.py widgets/base_widget.py widgets/clock_widget.py \
	     widgets/task_widget.py widgets/weather_widget.py widgets/music_widget.py \
	     widgets/system_widget.py widgets/note_widget.py /usr/share/widget-app/widgets/
	sudo cp widget-app.sh /usr/bin/widget-app
	sudo mkdir -p /usr/share/applications
	sudo cp widget-app.desktop /usr/share/applications/
	sudo mkdir -p /etc/xdg/autostart
	sudo cp widget-app-autostart.desktop /etc/xdg/autostart/widget-app.desktop
	@echo ""
	@echo "Installed. Run 'widget-app' to start. Widgets will auto-start on login."

uninstall:
	sudo rm -rf /usr/share/widget-app
	sudo rm -f /usr/bin/widget-app
	@echo "Uninstalled."
