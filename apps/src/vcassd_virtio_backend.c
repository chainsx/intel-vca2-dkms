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

#define _GNU_SOURCE

#include "helper_funcs.h"
#include "vcassd_virtio_backend.h"

void add_virtio_net_device(struct vca_info *vca)
{
	char path[PATH_MAX];
	struct vca_device_desc *dd = &virtnet_dev_page.dd;
	filehandle_t fd;
	int err;

	snprintf(path, PATH_MAX, "/dev/vop_virtio%d%d", vca->card_id, vca->cpu_id);
	fd = open(path, O_RDWR|O_CLOEXEC);
	if (fd < 0) {
		vcasslog("Could not open %s %s\n", path, strerror(errno));
		return;
	}

	err = ioctl(fd, VCA_VIRTIO_ADD_DEVICE, dd);
	if (err < 0) {
		vcasslog("Could not add %d %s\n", dd->type, strerror(errno));
		close(fd);
		return;
	}
	assert(dd->type == VIRTIO_ID_NET);
	vca->vca_net.virtio_net_fd = fd;
	vcasslog("Added VIRTIO_ID_NET for %s\n", vca->name);
}
