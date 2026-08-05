/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/device.h>
#include <zephyr/logging/log.h>
#include <zephyr/usb/usbd.h>

#ifdef CONFIG_USBD_BOS_SUPPORT
#include <zephyr/usb/msos_desc.h>
#endif /* CONFIG_USBD_BOS_SUPPORT */

LOG_MODULE_REGISTER(zpl_usb_backend);

#define ZPL_USB_VID			0x456	/* Analog Devices */
#define ZPL_USB_PID			0xaa55	/* Random PID */
#define ZPL_PRODUCT_MANUFACTURER	"Antmicro"
#define ZPL_PRODUCT_STRING		"Zephelin"
#define ZPL_USBD_MAX_POWER		100	/* 100 mA */
#define ZPL_MSOS_VENDOR_CODE	0x01U
#define ZPL_MSOS_WINDOWS_VERSION	0x0A000000UL

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

#ifdef CONFIG_USBD_BOS_SUPPORT

struct tracing_msosv2_descriptor {
	struct msosv2_descriptor_set_header header;
	struct msosv2_compatible_id compatible_id;
} __packed;

static const struct tracing_msosv2_descriptor tracing_msosv2_desc = {
	.header = {
		.wLength = sys_cpu_to_le16(sizeof(struct msosv2_descriptor_set_header)),
		.wDescriptorType = sys_cpu_to_le16(MS_OS_20_SET_HEADER_DESCRIPTOR),
		.dwWindowsVersion = sys_cpu_to_le32(ZPL_MSOS_WINDOWS_VERSION),
		.wTotalLength = sys_cpu_to_le16(sizeof(tracing_msosv2_desc)),
	},
	.compatible_id = {
		.wLength = sys_cpu_to_le16(sizeof(struct msosv2_compatible_id)),
		.wDescriptorType = sys_cpu_to_le16(MS_OS_20_FEATURE_COMPATIBLE_ID),
		.CompatibleID = {'W', 'I', 'N', 'U', 'S', 'B'},
	},
};

struct tracing_bos_msosv2_descriptor {
	struct usb_bos_platform_descriptor platform;
	struct usb_bos_capability_msos cap;
} __packed;

static const struct tracing_bos_msosv2_descriptor tracing_bos_msosv2_desc = {
	.platform = {
		.bLength = sizeof(struct tracing_bos_msosv2_descriptor),
		.bDescriptorType = USB_DESC_DEVICE_CAPABILITY,
		.bDevCapabilityType = USB_BOS_CAPABILITY_PLATFORM,
		.PlatformCapabilityUUID = {
			0xDF, 0x60, 0xDD, 0xD8, 0x89, 0x45, 0xC7, 0x4C,
			0x9C, 0xD2, 0x65, 0x9D, 0x9E, 0x64, 0x8A, 0x9F,
		},
	},
	.cap = {
		.dwWindowsVersion = sys_cpu_to_le32(ZPL_MSOS_WINDOWS_VERSION),
		.wMSOSDescriptorSetTotalLength = sys_cpu_to_le16(sizeof(tracing_msosv2_desc)),
		.bMS_VendorCode = ZPL_MSOS_VENDOR_CODE,
	},
};

static int tracing_msosv2_to_host(const struct usbd_context *const ctx,
				  const struct usb_setup_packet *const setup,
				  struct net_buf *const buf)
{
	ARG_UNUSED(ctx);

	if (setup->bRequest != ZPL_MSOS_VENDOR_CODE ||
	    setup->wIndex != MS_OS_20_DESCRIPTOR_INDEX) {
		return -ENOTSUP;
	}

	net_buf_add_mem(buf, &tracing_msosv2_desc,
			MIN(net_buf_tailroom(buf), sizeof(tracing_msosv2_desc)));

	return 0;
}

USBD_DESC_BOS_VREQ_DEFINE(tracing_bos_vreq_msosv2,
			  sizeof(tracing_bos_msosv2_desc), &tracing_bos_msosv2_desc,
			  ZPL_MSOS_VENDOR_CODE, tracing_msosv2_to_host, NULL);

#endif /* CONFIG_USBD_BOS_SUPPORT */

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

#ifdef CONFIG_USBD_BOS_SUPPORT
	ret = usbd_add_descriptor(&zpl_usbd, &tracing_bos_vreq_msosv2);
	if (ret) {
		LOG_ERR("Descriptors: failed to initialize BOS descriptor (%d)!", ret);
		return NULL;
	}

	ret = usbd_device_set_bcd_usb(&zpl_usbd, USBD_SPEED_FS, USB_SRN_2_0_1);
	if (ret) {
		LOG_ERR("Descriptors: Failed to set full-speed bcdUSB");
		return NULL;
	}
#endif /* CONFIG_USBD_BOS_SUPPORT */

	if (USBD_SUPPORTS_HIGH_SPEED && usbd_caps_speed(&zpl_usbd) == USBD_SPEED_HS) {
		ret = usbd_add_configuration(&zpl_usbd, USBD_SPEED_HS,
					     &zpl_hs_config);
		if (ret) {
			LOG_ERR("Configuration: Failed to add high-speed configuration");
			return NULL;
		}

#ifdef CONFIG_USBD_BOS_SUPPORT
		ret = usbd_device_set_bcd_usb(&zpl_usbd, USBD_SPEED_HS, USB_SRN_2_0_1);
		if (ret) {
			LOG_ERR("Descriptors: Failed to set high-speed bcdUSB");
			return NULL;
		}
#endif /* CONFIG_USBD_BOS_SUPPORT */

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
