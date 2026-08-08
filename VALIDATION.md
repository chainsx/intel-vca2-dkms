# Validation record

This source package was validated on 2026-08-08 with Linux
`7.0.0-28-generic` headers. This covers the post-6.11 `bus_type.match`,
post-6.14 `device_find_child` and BlockIO APIs, the post-6.18 IDA allocator
API, and the Linux 7.0 physical-address `dma_map_ops` callbacks.

Commands validated:

```bash
make -C /lib/modules/7.0.0-28-generic/build \
  M="$PWD/modules" VCA_BUILD_ROLE=node VCA_CARD_ARCH=l1om \
  KERNWARNFLAGS= modules

make -C /lib/modules/7.0.0-28-generic/build \
  M="$PWD/modules" VCA_BUILD_ROLE=host VCA_CARD_ARCH=l1om \
  KERNWARNFLAGS= modules
```

Results:

- node role: 15 VCA `.ko` files generated successfully;
- host role: 18 VCA `.ko` files generated successfully;
- shell syntax validation passed for the node DKMS maintainer scripts and
  initramfs hook;
- the source archive excludes all build products.

This does **not** establish runtime compatibility on a physical VCA2 node.
That requires node-image boot, CSA/VOP handshake, BlockIO, network, and
reboot validation on target hardware.
