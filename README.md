# Intel VCA2 DKMS host stack

This Debian source tree repackages Intel VCA 2.3.26 host software for Ubuntu 22.04 with local compatibility fixes.

It builds three binary packages:

- `vca2-vcass-modules-dkms`: DKMS source package for VCA2 host kernel modules.
- `daemon-vca`: userspace control programs and services (`vcactl`, `vcactld`, udev rules, configuration files).
- `vca2-host`: metapackage depending on the two packages above.

## Build dependencies

```bash
sudo apt update
sudo apt install -y \
  build-essential devscripts debhelper fakeroot dkms cmake g++ pkg-config python3 rsync \
  linux-headers-$(uname -r) linux-headers-generic \
  libboost-filesystem-dev libboost-thread-dev libboost-system-dev libboost-date-time-dev \
  libboost-chrono-dev libboost-atomic-dev bash-completion
```

## Build packages

```bash
dpkg-buildpackage -us -uc -b
```

or:

```bash
./build_debs.sh
```

Expected output in the parent directory:

```text
vca2-vcass-modules-dkms_2.3.26+ubuntu22.04.6_all.deb
daemon-vca_2.3.26+ubuntu22.04.6_amd64.deb
vca2-host_2.3.26+ubuntu22.04.6_all.deb
```

## Install

If an older local build is installed, remove it first:

```bash
sudo apt remove 'vca2-*' daemon-vca
sudo dkms remove -m vca2-vcass -v 2.3.26+ubuntu22.04.4 --all 2>/dev/null || true
sudo dkms remove -m vca2-vcass -v 2.3.26+ubuntu22.04.6 --all 2>/dev/null || true
```

Then install:

```bash
sudo apt install \
  ../vca2-vcass-modules-dkms_2.3.26+ubuntu22.04.6_all.deb \
  ../daemon-vca_2.3.26+ubuntu22.04.6_amd64.deb \
  ../vca2-host_2.3.26+ubuntu22.04.6_all.deb
```

## Load modules

```bash
sudo vca2-load-modules
```

The loader uses this order:

```text
vop_bus vop vca_csm_bus vca_mgr_bus vca_mgr_extd_bus vca_csa_bus
vca_virtio vca_virtio_ring vca_vringh vca_virtio_net
vcablkfe vcablk_bckend
vca_csm vca_mgr vca_mgr_extd
plx87xx_dma plx87xx
```

Do not load `vca_csa` on the host.

## Verify

```bash
find /lib/modules/$(uname -r)/updates/dkms -name 'vop.ko*' -o -name 'plx87xx.ko*'
sudo depmod -a
sudo modprobe vop
sudo modprobe plx87xx
sudo vcactl status
```

Expected base state after a successful host-side load:

```text
Card: 0 Cpu: 0 STATE: bios_up
Card: 0 Cpu: 1 STATE: bios_up
Card: 0 Cpu: 2 STATE: bios_up
```

## License

The Intel VCA module and application source trees contain `COPYING` with GNU GPL version 2. Source headers also state GNU GPL version 2. The Debian packaging is distributed under the same license. In Debian copyright notation this package is treated as `GPL-2` / GPL version 2.
