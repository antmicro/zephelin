/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/device.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/byteorder.h>
#include <zephyr/usb/usbd.h>
#include <zephyr/usb/bos.h>
#include <zephyr/usb/msos_desc.h>

LOG_MODULE_REGISTER(zpl_usb_backend);

#define ZPL_USB_VID			0x456	/* Analog Devices */
#define ZPL_USB_PID			0xaa55	/* Random PID */
#define ZPL_PRODUCT_MANUFACTURER	"Antmicro"
#define ZPL_PRODUCT_STRING		"Zephelin"
#define ZPL_USBD_MAX_POWER		100	/* 100 mA */

USBD_DEVICE_DEFINE(zpl_usbd,
		   DEVICE_DT_GET(DT_NODELABEL(zephyr_udc0)),
		   ZPL_USB_VID, ZPL_USB_PID);

/* USB Descriptors */
USBD_DESC_MANUFACTURER_DEFINE(zpl_mfr, ZPL_PRODUCT_MANUFACTURER);
USBD_DESC_PRODUCT_DEFINE(zpl_product, ZPL_PRODUCT_STRING);
USBD_DESC_CONFIG_DEFINE(fs_cfg_desc, "Zephelin Full-Speed Configuration");
USBD_DESC_CONFIG_DEFINE(hs_cfg_desc, "Zephelin High-Speed Configuration");

static const uint8_t attributes = 0;
static const char *blocklist[] = { NULL };

/* USB Configurations */
USBD_CONFIGURATION_DEFINE(zpl_fs_config, attributes, ZPL_USBD_MAX_POWER, &fs_cfg_desc);
USBD_CONFIGURATION_DEFINE(zpl_hs_config, attributes, ZPL_USBD_MAX_POWER, &hs_cfg_desc);

/*
 * Microsoft OS 2.0 descriptors: auto-bind WinUSB.sys to the vendor-specific
 * tracing interface so Windows recognizes it instead of showing an
 * "Unknown Device". Not needed on Linux, where libusb claims it directly.
 */
#define ZPL_MSOS2_VENDOR_CODE	0x01U
#define ZPL_MSOS2_OS_VERSION	0x0A000000UL	/* Windows 10 */

struct zpl_msosv2_descriptor {
	struct msosv2_descriptor_set_header header;
	struct msosv2_compatible_id compatible_id;
} __packed;

static struct zpl_msosv2_descriptor msosv2_desc = {
	.header = {
		.wLength = sizeof(struct msosv2_descriptor_set_header),
		.wDescriptorType = MS_OS_20_SET_HEADER_DESCRIPTOR,
		.dwWindowsVersion = sys_cpu_to_le32(ZPL_MSOS2_OS_VERSION),
		.wTotalLength = sizeof(msosv2_desc),
	},
	.compatible_id = {
		.wLength = sizeof(struct msosv2_compatible_id),
		.wDescriptorType = MS_OS_20_FEATURE_COMPATIBLE_ID,
		.CompatibleID = {'W', 'I', 'N', 'U', 'S', 'B', 0x00, 0x00},
	},
};

struct zpl_bos_msosv2_descriptor {
	struct usb_bos_platform_descriptor platform;
	struct usb_bos_capability_msos cap;
} __packed;

static struct zpl_bos_msosv2_descriptor bos_msosv2_desc = {
	.platform = {
		.bLength = sizeof(struct usb_bos_platform_descriptor)
			 + sizeof(struct usb_bos_capability_msos),
		.bDescriptorType = USB_DESC_DEVICE_CAPABILITY,
		.bDevCapabilityType = USB_BOS_CAPABILITY_PLATFORM,
		.bReserved = 0,
		/* MS OS 2.0 platform capability UUID
		 * D8DD60DF-4589-4CC7-9CD2-659D9E648A9F
		 */
		.PlatformCapabilityUUID = {
			0xDF, 0x60, 0xDD, 0xD8,
			0x89, 0x45,
			0xC7, 0x4C,
			0x9C, 0xD2,
			0x65, 0x9D, 0x9E, 0x64, 0x8A, 0x9F,
		},
	},
	.cap = {
		.dwWindowsVersion = sys_cpu_to_le32(ZPL_MSOS2_OS_VERSION),
		.wMSOSDescriptorSetTotalLength = sys_cpu_to_le16(sizeof(msosv2_desc)),
		.bMS_VendorCode = ZPL_MSOS2_VENDOR_CODE,
		.bAltEnumCode = 0x00,
	},
};

static int zpl_msosv2_to_host_cb(const struct usbd_context *const ctx,
				 const struct usb_setup_packet *const setup,
				 struct net_buf *const buf)
{
	ARG_UNUSED(ctx);

	if (setup->bRequest == ZPL_MSOS2_VENDOR_CODE &&
	    setup->wIndex == MS_OS_20_DESCRIPTOR_INDEX) {
		net_buf_add_mem(buf, &msosv2_desc,
				MIN(net_buf_tailroom(buf), sizeof(msosv2_desc)));
		return 0;
	}

	return -ENOTSUP;
}

USBD_DESC_BOS_VREQ_DEFINE(zpl_bos_vreq_msosv2, sizeof(bos_msosv2_desc), &bos_msosv2_desc,
			  ZPL_MSOS2_VENDOR_CODE, zpl_msosv2_to_host_cb, NULL);

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

	ret = usbd_add_descriptor(&zpl_usbd, &zpl_bos_vreq_msosv2);
	if (ret) {
		LOG_ERR("Descriptors: failed to add MS OS 2.0 descriptor (%d)!", ret);
		return NULL;
	}

	if (USBD_SUPPORTS_HIGH_SPEED && usbd_caps_speed(&zpl_usbd) == USBD_SPEED_HS) {
		ret = usbd_add_configuration(&zpl_usbd, USBD_SPEED_HS,
					     &zpl_hs_config);
		if (ret) {
			LOG_ERR("Configuration: Failed to add high-speed configuration");
			return NULL;
		}

		ret = usbd_register_all_classes(&zpl_usbd, USBD_SPEED_HS, 1,
						blocklist);
		if (ret) {
			LOG_ERR("Classes: failed to register classes (%d)!", ret);
			return NULL;
		}
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

	/* The stack only serves the BOS descriptor (and thus the MS OS 2.0
	 * capability) when bcdUSB >= 0x0201.
	 */
	usbd_device_set_bcd_usb(&zpl_usbd, USBD_SPEED_FS, USB_SRN_2_0_1);
	if (USBD_SUPPORTS_HIGH_SPEED && usbd_caps_speed(&zpl_usbd) == USBD_SPEED_HS) {
		usbd_device_set_bcd_usb(&zpl_usbd, USBD_SPEED_HS, USB_SRN_2_0_1);
	}

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
