#
# Intel VCA Software Stack (VCASS)
#
# Copyright(c) 2017 Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# The full GNU General Public License is included in this distribution in
# the file called "COPYING".
#
# Intel VCA Scripts.
#

define make_spec

%if "%dist" >= ".el7"
%define with_systemd 1
%define install_target systemd
%else
%define with_systemd 0
%define install_target no_systemd
%endif

Summary: Intel (R) VCA Management Daemon

%if "%dist" == ".el7.centos"
Name: $(name)
%else
Name: $(name)%dist
%endif
Version: %{_version}
Release: $(release)
License: See COPYING
Group: base
Vendor: Intel Corporation
URL: http://www.intel.com
Source0: $(name)-%{version}.tar.gz
%if ! %{defined module_headers_installed}
BuildRequires: vcass-modules-headers
%endif
Requires: mtools
Requires: pciutils
Requires: boost-regex boost-filesystem boost-date-time boost-thread boost-system
Requires: initscripts
Requires: bridge-utils
# resize_image.sh dependencies:
Requires: gdisk
Requires: coreutils
Requires: findutils
Requires: e2fsprogs
Requires: kpartx
Requires: gawk
Requires: util-linux
Requires: man
%description
vcactl-daemon provides the device management daemon and its control tool.
The daemon is responsible for booting the device, capturing crash dumps, etc.

%prep
%setup -D -q -c -T -a 0
%clean

%build
cmake -DOS=$(OS) -DPKG_VER=$(PKG_VER) -DDESTDIR=%{buildroot} -DBUILDNO=%{version} -DMODULES_SRC=$(modules_path) -G "Unix Makefiles"
$(make_prefix)%{__make} $(make_postfix) -j 12
%install
# installation depends on existence of systemd service, so first need to build additional targets
# (install_systemd for CentOS7X, install_no_systemd for CentOS6X), which install appropriate files,
# then install rest of required files
%{__make} install_%{install_target} install sysconfdir=/etc
mkdir -p %{buildroot}/var/run/lock/vca
mkdir -p %{buildroot}/usr/share/man/man1
gzip -c vcactl.1 > %{buildroot}/usr/share/man/man1/vcactl.1.gz
%pre
systemctl disable NetworkManager --now

if [ $$1 == 1 ]; then
    if [ -z `getent group vcausers` ] ; then
        groupadd vcausers
    fi

    if [ -z `getent passwd vcausers_default` ] ; then
        adduser -r vcausers_default -g vcausers
    fi
fi

if [ ! -d /var/log/vca ]; then
	mkdir -p /var/log/vca
	chgrp vcausers /var/log/vca
	chmod 775 /var/log/vca
fi

%post
if [ $$1 == 1 ]; then
%if %with_systemd
	systemctl enable vcactl
%else
	chkconfig --add vcactl
%endif
	ln -s /usr/sbin/vcactl /usr/sbin/vcactrl
	chgrp vcausers /etc/vca_config.d/
	chmod 775 /etc/vca_config.d/
elif [ $$1 -gt 1 ]; then
	mv /var/log/vcactld      /var/log/vca/vcactld.log  2>/dev/null || true
	mv /var/log/vca_ifup_log /var/log/vca/vca_ifup.log 2>/dev/null || true
fi

if [ -a /etc/vca_config.d/vca_config.old_user.xml ]; then
	cp /etc/vca_config.d/vca_config.xml /etc/vca_config.d/vca_config.new_default.xml
	echo "Running configuration update. This may take a while."
	vca_config_upgrade.sh
fi

%preun
vcactl blockio list | while read card cpu blk state mode; do case $$state in
enabled) vcactl blockio close $$card $$cpu $$blk ;;
esac ; done
rm -f /etc/vca_config.d/vca_config.old_user.xml /etc/vca_config.d/vca_config.old_default.xml
cp /etc/vca_config.d/vca_config.xml /etc/vca_config.d/vca_config.old_user.xml
vcactl config-default
cp /etc/vca_config.d/vca_config.xml /etc/vca_config.d/vca_config.old_default.xml
if [ $$1 == 0 ]; then
%if %with_systemd
	systemctl disable vcactl
%else
	chkconfig --del vcactl
%endif
        [ -L /usr/sbin/vcactrl ] && unlink /usr/sbin/vcactrl
fi

%files
%exclude /usr/lib/vca/*.pyc
%exclude /usr/lib/vca/*.pyo
%defattr(750,root,vcausers,-)
/usr/sbin/vcactld
/usr/sbin/vcactl
/usr/sbin/vca_start_card_domu.sh
/usr/sbin/vca_start_card_kvm.sh
/usr/sbin/vca_kvmgtctl.sh
/usr/sbin/vca_config_upgrade.sh
/usr/sbin/vca_image_resize.sh
/usr/sbin/vcainfo
%attr(754,root,root) /usr/sbin/vca_eth_ifup.sh
%defattr(660,root,vcausers,775)
%config /etc/vca_config.d/vca_config.xml
%config /etc/vca_config.d/vca_xen_multicast_config.xml
/etc/vca_config.d/MACUpdateImage.img
/etc/vca_config.d/ClearSMBiosEventLogImage.img
%defattr(754,root,vcausers,775)
/etc/vca_config.d/vca_auto_boot.sh
/etc/vca_config.d/vca_daemon_default.sh
%defattr(644,root,root,-)
/lib/udev/rules.d/95-vca.rules
/lib/udev/rules.d/96-vop.rules
/lib/udev/rules.d/97-host_eth_up.rules
/lib/udev/rules.d/98-vca_mgr.rules
/lib/udev/rules.d/99-vca_mgr_extd.rules
/lib/udev/rules.d/99-vca_blk_bcknd.rules
/usr/lib/vca/card_vm.hvm
/usr/lib/vca/card_gfx_vm.hvm
/usr/lib/vca/windows_card_gfx_vm.hvm
/usr/lib/vca/vcanodeinfo.sh
/usr/share/bash-completion/completions/vcactl
/usr/share/man/man1/vcactl.1.gz
/usr/lib/tmpfiles.d/vca.conf
%attr(775,root,vcausers) /var/run/lock/vca
%defattr(770,root,vcausers,775)
/usr/lib/vca/domUsetup.sh
/usr/lib/vca/kvmsetup.sh
/usr/lib/vca/kvmgtctl_node.sh
/usr/lib/vca/make_config.py
%if %with_systemd
%defattr(644,root,root,-)
/usr/lib/systemd/system/vcactl.service
%else
%defattr(755,root,root,-)
/etc/rc.d/init.d/vcactl
%endif
%attr(775,root,root)  /etc/profile.d/vcausers_setup_path.sh
%changelog

endef

export make_spec
