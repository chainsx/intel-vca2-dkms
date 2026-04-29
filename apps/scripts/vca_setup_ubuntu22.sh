#!/bin/bash
# Ubuntu 22.04 helper installer for Intel VCA user-space tools.
# Run from the source tree after building, or pass --build-dir <dir>.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${SRC_DIR}/build"
START_SERVICE=0
OVERWRITE_CONFIG=0

usage() {
    cat <<USAGE
Usage: sudo $0 [--build-dir DIR] [--start] [--overwrite-config]

Installs vcactl/vcactld, default configuration, udev rules, systemd service,
and creates the vcausers group plus vcausers_default system user.
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --build-dir)
            BUILD_DIR="$2"; shift 2 ;;
        --start)
            START_SERVICE=1; shift ;;
        --overwrite-config)
            OVERWRITE_CONFIG=1; shift ;;
        -h|--help)
            usage; exit 0 ;;
        *)
            echo "Unknown argument: $1" >&2; usage; exit 2 ;;
    esac
done

if [[ ${EUID} -ne 0 ]]; then
    echo "This installer must be run as root." >&2
    exit 1
fi

if [[ ! -x "${BUILD_DIR}/bin/vcactl" || ! -x "${BUILD_DIR}/bin/vcactld" ]]; then
    echo "Cannot find built binaries in ${BUILD_DIR}/bin." >&2
    echo "Build first, for example:" >&2
    echo "  mkdir -p build && cd build" >&2
    echo "  cmake .. -DOS=UBUNTU -DPKG_VER=2.3.26-ubuntu22.04-py3-v3 -DMODULES_SRC=/path/to/vca_modules" >&2
    echo "  make -j\"\$(nproc)\"" >&2
    exit 1
fi

if ! getent group vcausers >/dev/null; then
    groupadd --system vcausers
fi

if ! getent passwd vcausers_default >/dev/null; then
    adduser --system --no-create-home --ingroup vcausers --disabled-login --disabled-password vcausers_default
fi

install -d -m 0755 /usr/sbin
install -m 0755 "${BUILD_DIR}/bin/vcactl" /usr/sbin/vcactl
install -m 0755 "${BUILD_DIR}/bin/vcactld" /usr/sbin/vcactld
ln -sfn /usr/sbin/vcactl /usr/sbin/vcactrl

install -d -m 0775 -o root -g vcausers /etc/vca_config.d
for f in vca_config.xml vca_xen_multicast_config.xml; do
    if [[ -f "/etc/vca_config.d/${f}" && ${OVERWRITE_CONFIG} -eq 0 ]]; then
        echo "Keeping existing /etc/vca_config.d/${f}"
    else
        install -m 0664 -o root -g vcausers "${SRC_DIR}/vca_config.d/${f}" "/etc/vca_config.d/${f}"
    fi
done
for f in vca_daemon_default.sh vca_auto_boot.sh; do
    install -m 0750 -o root -g vcausers "${SRC_DIR}/vca_config.d/${f}" "/etc/vca_config.d/${f}"
done
for f in MACUpdateImage.img ClearSMBiosEventLogImage.img; do
    install -m 0660 -o root -g vcausers "${SRC_DIR}/vca_config.d/${f}" "/etc/vca_config.d/${f}"
done

install -d -m 0775 -o root -g vcausers /var/log/vca
install -d -m 0775 -o root -g vcausers /var/lock/vca
install -d -m 0775 -o root -g vcausers /run/lock/vca

install -d -m 0755 /lib/udev/rules.d
install -m 0644 "${SRC_DIR}/rules/95-vca.rules" /lib/udev/rules.d/95-vca.rules
install -m 0644 "${SRC_DIR}/rules/96-vop.rules" /lib/udev/rules.d/96-vop.rules
install -m 0644 "${SRC_DIR}/rules/97-host_eth_up.rules" /lib/udev/rules.d/97-host_eth_up.rules
install -m 0644 "${SRC_DIR}/rules/98-vca_mgr.rules" /lib/udev/rules.d/98-vca_mgr.rules
install -m 0644 "${SRC_DIR}/rules/99-vca_mgr_extd.rules" /lib/udev/rules.d/99-vca_mgr_extd.rules
install -m 0644 "${SRC_DIR}/rules/99-vca_blk_bcknd.rules" /lib/udev/rules.d/99-vca_blk_bcknd.rules

install -d -m 0755 /lib/systemd/system
install -m 0644 "${SRC_DIR}/services/vcactl.service" /lib/systemd/system/vcactl.service

install -d -m 0755 /usr/lib/vca
install -m 0774 "${SRC_DIR}/scripts/vca_eth_ifup.sh" /usr/sbin/vca_eth_ifup.sh
install -m 0774 "${SRC_DIR}/scripts/vca_config_upgrade.sh" /usr/sbin/vca_config_upgrade.sh
install -m 0774 "${SRC_DIR}/scripts/make_config.py" /usr/lib/vca/make_config.py
install -m 0750 "${SRC_DIR}/tools/vcainfo" /usr/sbin/vcainfo
install -m 0750 "${SRC_DIR}/tools/vca_image_resize.sh" /usr/sbin/vca_image_resize.sh
install -m 0750 "${SRC_DIR}/tools/vcanodeinfo.sh" /usr/lib/vca/vcanodeinfo.sh

if command -v systemd-tmpfiles >/dev/null 2>&1; then
    install -d -m 0755 /usr/lib/tmpfiles.d
    install -m 0644 "${SRC_DIR}/tmpfiles.d/vca.conf" /usr/lib/tmpfiles.d/vca.conf
    systemd-tmpfiles --create /usr/lib/tmpfiles.d/vca.conf || true
fi

udevadm control --reload-rules || true
udevadm trigger --subsystem-match=vca_csm_bus --subsystem-match=vca_mgr_bus --subsystem-match=vca_mgr_extd_bus 2>/dev/null || true
systemctl daemon-reload || true

if [[ ${START_SERVICE} -eq 1 ]]; then
    systemctl enable vcactl.service
    systemctl restart vcactl.service
fi

echo "VCA user-space installation complete."
echo "Try: sudo vcactl status"
