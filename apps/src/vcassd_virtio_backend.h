/*
* Intel VCA Software Stack (VCASS)
*
* Copyright(c) 2015-2018 Intel Corporation.
*
* This program is free software; you can redistribute it and/or modify
* it under the terms of the GNU General Public License, version 2, as
* published by the Free Software Foundation.
*
* This program is distributed in the hope that it will be useful, but
* WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
* General Public License for more details.
*
* The full GNU General Public License is included in this distribution in
* the file called "COPYING".
*
* Intel VCA User Space Tools.
*/

#ifndef _VCASSD_VIRTIO_BACKEND_H_
#define _VCASSD_VIRTIO_BACKEND_H_

#include <sys/ioctl.h>

struct virtio_device;
/* uapi/vca_virtio_net.h includes include/vca_virtio_config.h header
 * which is not necessary, but triggers cascade of additional dependencies
 * which are hard to met without kernel source, which we do not want to
 * depend on (directly)
 *
 * following line prevents such file inclusion */
#define _VCA_LINUX_VIRTIO_CONFIG_H
#include "vca_virtio_net.h"

#include "vcassd_common.h"
#include <vca_dev_common.h>
#include <vca_ioctl.h>

#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))

#ifndef VCA_HTOLE16_CONST
# if defined(__BYTE_ORDER__) && (__BYTE_ORDER__ == __ORDER_BIG_ENDIAN__)
#  define VCA_HTOLE16_CONST(x) ((__u16)__builtin_bswap16((__u16)(x)))
#  define VCA_HTOLE32_CONST(x) ((__u32)__builtin_bswap32((__u32)(x)))
# else
#  define VCA_HTOLE16_CONST(x) ((__u16)(x))
#  define VCA_HTOLE32_CONST(x) ((__u32)(x))
# endif
#endif

#define GSO_ENABLED		0
#define MAX_GSO_SIZE		(64 * 1024)
#define ETH_H_LEN		14

/* Publish dma mapped addresses in the desc ring */
#define VIRTIO_RING_F_DMA_MAP          30

#ifndef VIRTIO_NET_F_OFFSET_RXBUF
#define VIRTIO_NET_F_OFFSET_RXBUF	24	/* Set offset in receive buffer */
#endif

static struct {
	struct vca_device_desc dd;
	struct vca_vqconfig vqconfig[2];
	__u32 host_features, guest_acknowledgements;
	struct virtio_net_config net_config;
} virtnet_dev_page = {
	.dd = {
	.type = VIRTIO_ID_NET,
	.num_vq = ARRAY_SIZE(virtnet_dev_page.vqconfig),
	.feature_len = sizeof(virtnet_dev_page.host_features),
	.config_len = sizeof(virtnet_dev_page.net_config),
},
.vqconfig[0] = {
	.num = VCA_HTOLE16_CONST(VCA_VRING_ENTRIES),
},
.vqconfig[1] = {
	.num = VCA_HTOLE16_CONST(VCA_VRING_ENTRIES),
},
#if GSO_ENABLED
.host_features = VCA_HTOLE32_CONST(
	1 << VIRTIO_NET_F_CSUM |
	1 << VIRTIO_NET_F_GSO |
	1 << VIRTIO_NET_F_GUEST_TSO4 |
	1 << VIRTIO_NET_F_GUEST_TSO6 |
	1 << VIRTIO_NET_F_GUEST_ECN |
	1 << VIRTIO_RING_F_DMA_MAP |
	1 << VIRTIO_NET_F_GUEST_UFO),
#else
.host_features = VCA_HTOLE32_CONST(
	1 << VIRTIO_RING_F_DMA_MAP |
	1 << VIRTIO_NET_F_OFFSET_RXBUF
	),
#endif
};

void add_virtio_net_device(struct vca_info *vca);

#endif
