# Validation record

This source package was validated on 2026-07-03 with Linux
`6.12.74+deb13+1-amd64` headers. This is a proxy build environment that
contains the post-6.11 `bus_type.match`, post-6.14 `device_find_child`, and
post-6.14 BlockIO APIs relevant to Ubuntu 24.04 HWE Linux 6.17.

Commands validated:

```bash
make -C /lib/modules/6.12.74+deb13+1-amd64/build \
  M="$PWD/modules" VCA_BUILD_ROLE=node VCA_CARD_ARCH=l1om \
  KERNWARNFLAGS= modules

make -C /lib/modules/6.12.74+deb13+1-amd64/build \
  M="$PWD/modules" VCA_BUILD_ROLE=host VCA_CARD_ARCH=l1om \
  KERNWARNFLAGS= modules
```

Results:

- node role: 15 VCA `.ko` files generated successfully;
- host role: 18 VCA `.ko` files generated successfully;
- shell syntax validation passed for the node DKMS maintainer scripts and
  initramfs hook;
- the source archive excludes all build products.

This does **not** establish runtime compatibility on a physical VCA2 node or
an actual Ubuntu 6.17 node kernel. Those require node-image boot, CSA/VOP
handshake, BlockIO, network, and reboot validation on target hardware.
