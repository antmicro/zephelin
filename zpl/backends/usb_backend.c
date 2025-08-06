/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/device.h>
#include <zephyr/logging/log.h>
#include <zephyr/usb/usbd.h>

LOG_MODULE_REGISTER(zpl_usb_backend);

#define ZPL_USB_VID			0x456	/* Analog Devices */
#define ZPL_USB_PID			0xaa55	/* Random PID */
#define ZPL_PRODUCT_MANUFACTURER	"Antmicro"
#define ZPL_PRODUCT_STRING		"Zeppelin"
#define ZPL_USBD_MAX_POWER		100	/* 100 mA */

USBD_DEVICE_DEFINE(zpl_usbd,
		   DEVICE_DT_GET(DT_NODELABEL(zephyr_udc0)),
		   ZPL_USB_VID, ZPL_USB_PID);

/* USB Descriptors */
USBD_DESC_MANUFACTURER_DEFINE(zpl_mfr, ZPL_PRODUCT_MANUFACTURER);
USBD_DESC_PRODUCT_DEFINE(zpl_product, ZPL_PRODUCT_STRING);
USBD_DESC_CONFIG_DEFINE(fs_cfg_desc, "Zeppelin Full-Speed Configuration");

static const uint8_t attributes = 0;
static const char *blocklist[] = { NULL };

/* USB Configurations */
USBD_CONFIGURATION_DEFINE(zpl_fs_config, attributes, ZPL_USBD_MAX_POWER, &fs_cfg_desc);

static struct usbd_context *zpl_usbd_setup_device(void)
{
	int ret;

	ret = usbd_add_descriptor(&zpl_usbd, &zpl_mfr);
	if (ret) {
		LOG_ERR("Descriptors: failed to initialize manufacturer descriptor (%d)!", ret);
		return NULL;
	}

	ret = usbd_add_descriptor(&zpl_usbd, &zpl_product);
	if (ret) {
		LOG_ERR("Descriptors: failed to initialize product descriptor (%d)!", ret);
		return NULL;
	}

	ret = usbd_add_configuration(&zpl_usbd, USBD_SPEED_FS, &zpl_fs_config);
	if (ret) {
		LOG_ERR("Configuration: failed to add full-speed configuration (%d)!", ret);
		return NULL;
	}

	ret = usbd_register_all_classes(&zpl_usbd, USBD_SPEED_FS, 1, blocklist);
	if (ret) {
		LOG_ERR("Classes: failed to add register classes (%d)!", ret);
		return NULL;
	}

	usbd_device_set_code_triple(&zpl_usbd, USBD_SPEED_FS, 0, 0, 0);
	usbd_self_powered(&zpl_usbd, attributes & USB_SCD_SELF_POWERED);

	return &zpl_usbd;
}

struct usbd_context *zpl_usbd_init_device(void)
{
	int ret;
	struct usbd_context *ctx;

	ctx = zpl_usbd_setup_device();
	if (!ctx) {
		LOG_ERR("Failed to setup USB device context!");
		return NULL;
	}

	ret = usbd_init(&zpl_usbd);
	if (ret) {
		LOG_ERR("Failed to initialize device support!");
		return NULL;
	}

	return &zpl_usbd;
}
