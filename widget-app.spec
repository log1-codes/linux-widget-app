%global appname widget-app

Name:           widget-app
Version:        1.0.0
Release:        1%{?dist}
Summary:        Desktop widgets for developers (clock, tasks, weather, music, system, notes)

License:        MIT
URL:            https://github.com/singhanurag/widget-app
Source0:        %{appname}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel

Requires:       python3
Requires:       python3-gobject
Requires:       python3-psutil
Requires:       python3-requests
Requires:       python3-dbus
Requires:       gtk3
Requires:       dbus
Requires:       dbus-libs

%description
A collection of desktop widgets including an analog clock, task list,
weather forecast, music now-playing (MPRIS), system monitor (CPU/RAM/disk),
and quick notes. All widgets are draggable and resizable on your desktop.

%prep
%setup -q -n %{appname}-%{version}

%install
install -dm 0755 %{buildroot}%{_datadir}/%{appname}
install -dm 0755 %{buildroot}%{_datadir}/%{appname}/manager
install -dm 0755 %{buildroot}%{_datadir}/%{appname}/widgets

install -pm 0644 main.py %{buildroot}%{_datadir}/%{appname}/
install -pm 0644 manager/__init__.py %{buildroot}%{_datadir}/%{appname}/manager/
install -pm 0644 manager/widget_manager.py %{buildroot}%{_datadir}/%{appname}/manager/
install -pm 0644 widgets/__init__.py %{buildroot}%{_datadir}/%{appname}/widgets/
install -pm 0644 widgets/base_widget.py %{buildroot}%{_datadir}/%{appname}/widgets/
install -pm 0644 widgets/clock_widget.py %{buildroot}%{_datadir}/%{appname}/widgets/
install -pm 0644 widgets/task_widget.py %{buildroot}%{_datadir}/%{appname}/widgets/
install -pm 0644 widgets/weather_widget.py %{buildroot}%{_datadir}/%{appname}/widgets/
install -pm 0644 widgets/music_widget.py %{buildroot}%{_datadir}/%{appname}/widgets/
install -pm 0644 widgets/system_widget.py %{buildroot}%{_datadir}/%{appname}/widgets/
install -pm 0644 widgets/note_widget.py %{buildroot}%{_datadir}/%{appname}/widgets/

install -pm 0755 widget-app.sh %{buildroot}%{_bindir}/widget-app

install -dm 0755 %{buildroot}%{_datadir}/applications
install -pm 0644 widget-app.desktop %{buildroot}%{_datadir}/applications/

install -dm 0755 %{buildroot}%{_sysconfdir}/xdg/autostart
install -pm 0644 widget-app-autostart.desktop %{buildroot}%{_sysconfdir}/xdg/autostart/widget-app.desktop

%files
%{_datadir}/%{appname}/
%{_bindir}/widget-app
%{_datadir}/applications/%{appname}.desktop
%{_sysconfdir}/xdg/autostart/widget-app.desktop

%changelog
* Tue May 12 2026  <singhanurag@fedoraproject.org> - 1.0.0-1
- Initial RPM release
