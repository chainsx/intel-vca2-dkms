/* SPDX-License-Identifier: GPL-2.0
 * Compatibility shims for building Intel VCA 2.3.26 modules against
 * Ubuntu 24.04 GA (Linux 6.8) and HWE (Linux 6.17) kernels.
 */
#ifndef VCA_LINUX_6X_COMPAT_H
#define VCA_LINUX_6X_COMPAT_H

#include <linux/version.h>
#include <linux/compiler.h>
#include <linux/dma-mapping.h>
#include <linux/io.h>
#include <linux/idr.h>
#include <linux/printk.h>
#include <linux/slab.h>
#include <linux/string.h>
#include <linux/time64.h>
#include <linux/timekeeping.h>
#include <linux/types.h>

#ifndef pr_warning
#define pr_warning pr_warn
#endif

#ifndef ACCESS_ONCE
#define ACCESS_ONCE(x) (*(volatile typeof(x) *)&(x))
#endif

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 9, 0)
#ifndef kzfree
#define kzfree(p) kfree_sensitive(p)
#endif
#endif

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 18, 0)
#define pci_set_dma_mask(pdev, mask) dma_set_mask(&(pdev)->dev, (mask))
#define pci_set_consistent_dma_mask(pdev, mask) dma_set_coherent_mask(&(pdev)->dev, (mask))
#endif

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 0, 0)
#define dma_zalloc_coherent(dev, size, dma_handle, gfp)                 \
({                                                                      \
        void *__vca_dma_zalloc_ptr;                                     \
        __vca_dma_zalloc_ptr = dma_alloc_coherent((dev), (size),        \
                                                  (dma_handle), (gfp)); \
        if (__vca_dma_zalloc_ptr)                                       \
                memset(__vca_dma_zalloc_ptr, 0, (size));                \
        __vca_dma_zalloc_ptr;                                           \
})
#endif


/*
 * VCA_LINUX_6_18_IDA_COMPAT
 *
 * Linux 6.18 no longer exports the legacy ida_simple_get()/
 * ida_simple_remove() API used by the VCA 2.3.26 sources.  Keep the legacy
 * call sites intact, but map them to the supported IDA allocator APIs.
 */
#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 18, 0)
static inline int vca_ida_simple_get(struct ida *ida, unsigned int start,
				     unsigned int end, gfp_t gfp_mask)
{
	if (end)
		return ida_alloc_range(ida, start, end - 1, gfp_mask);

	return ida_alloc_min(ida, start, gfp_mask);
}

static inline void vca_ida_simple_remove(struct ida *ida, unsigned int id)
{
	ida_free(ida, id);
}

#define ida_simple_get(ida, start, end, gfp_mask) \
	vca_ida_simple_get((ida), (start), (end), (gfp_mask))
#define ida_simple_remove(ida, id) \
	vca_ida_simple_remove((ida), (id))
#endif

#endif /* VCA_LINUX_6X_COMPAT_H */
