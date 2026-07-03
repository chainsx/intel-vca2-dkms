# VCA2 node-side DKMS package

`vca2-vcass-node-modules-dkms` is for the Linux system running inside a VCA2
node. It is not for the Ubuntu host with the PCIe card.

## What it installs

- a separate DKMS source tree: `/usr/src/vca2-vcass-node-<version>`;
- card-side PLX, VOP, CSA, VCA virtio, and BlockIO modules;
- `/usr/sbin/vca_agent.sh` and `vca_agent.service`;
- node-specific modprobe/modules-load configuration;
- an initramfs-tools hook that includes the early VCA transport and BlockIO
  modules.

The DKMS build is explicitly card-side:

```bash
make VCA_BUILD_ROLE=node VCA_CARD_ARCH=l1om \
  KERNEL_VERSION="${kernelver}" \
  KERNEL_SRC="/lib/modules/${kernelver}/build" \
  KERNWARNFLAGS= modules
```

## Installing into a booted node

Install the matching kernel headers first, then the package:

```bash
sudo apt install dkms build-essential initramfs-tools \
  "linux-headers-$(uname -r)"
sudo apt install ./vca2-vcass-node-modules-dkms_2.3.26+ubuntu24.04.9_all.deb
sudo dkms autoinstall -k "$(uname -r)"
sudo depmod -a "$(uname -r)"
sudo update-initramfs -u -k "$(uname -r)"
```

## Image build requirement

A node package alone does not make an arbitrary Ubuntu rootfs bootable on a
VCA2 node. The node image must also have a compatible EFI/GRUB configuration,
a kernel, a matching root device configuration, and the generated initramfs.
For a BlockIO-root image, build the DKMS modules and initramfs *inside the node
root filesystem* before the image is finalized. Ensure `vcablkfe`, `vop`,
`vca_csa`, VCA virtio modules, `plx87xx_dma`, and `plx87xx` are present in the
initramfs.

Do not install this package into the PCIe host: it installs `vca_csa`, whereas
the host uses `vca_csm` and the two drivers compete for the VCA sysfs class.
