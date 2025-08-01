#include <zephyr/fff.h>
#include <zephyr/ztest.h>
#include <zephyr/usb/usbd.h>
#include <zpl/usb_backend.h>

/* This typedef is needed for the `usbd_register_all_class()` function mock */
typedef const char * const * blocklist_t;

DEFINE_FFF_GLOBALS;

FAKE_VALUE_FUNC(int, usbd_add_configuration, struct usbd_context *, const enum usbd_speed, struct usbd_config_node *);
FAKE_VALUE_FUNC(int, usbd_add_descriptor, struct usbd_context *, struct usbd_desc_node *);
FAKE_VALUE_FUNC(int, usbd_device_set_code_triple, struct usbd_context *, const enum usbd_speed, const uint8_t, const uint8_t, const uint8_t);
FAKE_VALUE_FUNC(int, usbd_init, struct usbd_context *);
FAKE_VOID_FUNC(usbd_self_powered, struct usbd_context *, const bool);
FAKE_VALUE_FUNC(int, usbd_register_all_classes, struct usbd_context *, const enum usbd_speed, uint8_t, blocklist_t);

ZTEST(zpl_usb_backend, test_zpl_usbd_init_device_pass)
{
	usbd_add_descriptor_fake.return_val = 0;
	usbd_add_configuration_fake.return_val = 0;
	usbd_device_set_code_triple_fake.return_val = 0;
	usbd_init_fake.return_val = 0;
	usbd_register_all_classes_fake.return_val = 0;

	zassert_not_equal(zpl_usbd_init_device(), NULL,
			"zpl_usbd_init_device() should have succeeded!");
}

ZTEST(zpl_usb_backend, test_zpl_usbd_init_device_fail_add_descriptor)
{
	usbd_add_descriptor_fake.return_val = 1;
	usbd_add_configuration_fake.return_val = 0;
	usbd_device_set_code_triple_fake.return_val = 0;
	usbd_init_fake.return_val = 0;
	usbd_register_all_classes_fake.return_val = 0;

	zassert_equal(zpl_usbd_init_device(), NULL,
			"zpl_usbd_init_device() should have failed on usbd_add_descriptor()!");
}

ZTEST(zpl_usb_backend, test_zpl_usbd_init_device_fail_add_configuration)
{
	usbd_add_descriptor_fake.return_val = 0;
	usbd_add_configuration_fake.return_val = 1;
	usbd_device_set_code_triple_fake.return_val = 0;
	usbd_init_fake.return_val = 0;
	usbd_register_all_classes_fake.return_val = 0;

	zassert_equal(zpl_usbd_init_device(), NULL,
			"zpl_usbd_init_device() should have failed on usbd_add_configuration()!");
}

ZTEST(zpl_usb_backend, test_zpl_usbd_init_device_fail_usbd_init)
{
	usbd_add_descriptor_fake.return_val = 0;
	usbd_add_configuration_fake.return_val = 0;
	usbd_device_set_code_triple_fake.return_val = 0;
	usbd_init_fake.return_val = 1;
	usbd_register_all_classes_fake.return_val = 0;

	zassert_equal(zpl_usbd_init_device(), NULL,
			"zpl_usbd_init_device() should have failed on usbd_init()!");
}

ZTEST(zpl_usb_backend, test_zpl_usbd_init_device_fail_usbd_register_all_classes)
{
	usbd_add_descriptor_fake.return_val = 0;
	usbd_add_configuration_fake.return_val = 0;
	usbd_device_set_code_triple_fake.return_val = 0;
	usbd_init_fake.return_val = 0;
	usbd_register_all_classes_fake.return_val = 1;

	zassert_equal(zpl_usbd_init_device(), NULL,
			"zpl_usbd_init_device() should have failed on usbd_register_all_classes()!");
}

ZTEST_SUITE(zpl_usb_backend, NULL, NULL, NULL, NULL, NULL);
