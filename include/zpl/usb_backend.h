/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#ifndef ZPL_USB_BACKEND_H_
#define ZPL_USB_BACKEND_H_

#ifdef __cplusplus
extern "C" {
#endif

struct usbd_context *zpl_usbd_init_device(void);

#ifdef __cplusplus
}
#endif

#endif /* ZPL_USB_BACKEND_H_ */
