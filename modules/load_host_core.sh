#!/bin/sh
set -eu
base="$(dirname "$0")"
insmod "$base/vca/bus/vop_bus.ko" || true
insmod "$base/vca/bus/vca_csm_bus.ko" || true
insmod "$base/vca/bus/vca_mgr_bus.ko" || true
insmod "$base/vca/bus/vca_mgr_extd_bus.ko" || true
insmod "$base/vca/bus/vca_csa_bus.ko" || true

insmod "$base/vca/vca_virtio/vca_virtio.ko" || true
insmod "$base/vca/vca_virtio/vca_virtio_ring.ko" || true
insmod "$base/vca/vca_virtio/vca_vringh.ko" || true
insmod "$base/vca/vca_virtio/vca_virtio_net.ko" || true

insmod "$base/vca/vca_csm/vca_csm.ko" || true
insmod "$base/vca/vca_mgr/vca_mgr.ko" || true
insmod "$base/vca/vca_mgr_extd/vca_mgr_extd.ko" || true

# Host side: do not load vca/vca_csa/vca_csa.ko. It creates a duplicate /sys/class/vca.
# BlockIO modules must be loaded before plx87xx because BlockIO is enabled by default,
# because plx87xx resolves vcablk frontend/backend symbols at load time.
[ -f "$base/vca/blockio/vcablkfe.ko" ] && insmod "$base/vca/blockio/vcablkfe.ko" || true
[ -f "$base/vca/blockio/vcablk_bckend.ko" ] && insmod "$base/vca/blockio/vcablk_bckend.ko" || true

insmod "$base/vca/plx87xx_dma/plx87xx_dma.ko" || true
insmod "$base/plx87xx.ko" || true
