/* SPDX-License-Identifier: GPL-2.0
 * Compatibility shims for building Intel VCA 2.3.26 modules against
 * Ubuntu 22.04 HWE / Linux 6.8 kernels.
 */
#ifndef VCA_LINUX_6X_COMPAT_H
#define VCA_LINUX_6X_COMPAT_H

#include <linux/version.h>
#include <linux/compiler.h>
#include <linux/dma-mapping.h>
#include <linux/io.h>
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

#endif /* VCA_LINUX_6X_COMPAT_H */
