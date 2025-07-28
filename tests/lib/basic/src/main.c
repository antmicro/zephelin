#include <zephyr/fff.h>
#include <zephyr/ztest.h>
#include <zephyr/usb/usbd.h>

#include <zpl/lib.h>
#include <zpl/configuration.h>

#ifdef CONFIG_ZPL_TRACE_BACKEND_USB
DEFINE_FFF_GLOBALS;
FAKE_VALUE_FUNC(struct usbd_context *, zpl_usbd_init_device);
FAKE_VALUE_FUNC(int, usbd_enable, struct usbd_context *);
#endif

ZTEST(zpl, test_library_init_succeed)
{
#ifdef CONFIG_ZPL_TRACE_BACKEND_USB
	struct usbd_context ctx;

	RESET_FAKE(zpl_usbd_init_device);
	RESET_FAKE(usbd_enable);
	zpl_usbd_init_device_fake.return_val = &ctx;
	usbd_enable_fake.return_val = 0;
#endif /* CONFIG_ZPL_TRACE_BACKEND_USB */

	zassert_equal(0, zpl_init(),
			"zpl_init() failed to initialize");
}

#ifdef CONFIG_ZPL_TRACE_BACKEND_USB
ZTEST(zpl, test_library_init_fail)
{
	struct usbd_context ctx;

	RESET_FAKE(zpl_usbd_init_device);
	RESET_FAKE(usbd_enable);
	zpl_usbd_init_device_fake.return_val = &ctx;
	usbd_enable_fake.return_val = -EINVAL;

	zassert_equal(1, zpl_init(),
			"zpl_init() was expected to fail");

	RESET_FAKE(zpl_usbd_init_device);
	RESET_FAKE(usbd_enable);
	zpl_usbd_init_device_fake.return_val = NULL;
	usbd_enable_fake.return_val = 0;

	zassert_equal(1, zpl_init(),
			"zpl_init() was expected to fail");
}
#endif /* CONFIG_ZPL_TRACE_BACKEND_USB */

ZTEST(zpl, test_runtime_check_conf)
{
	zassert_equal(IS_ENABLED(CONFIG_ZPL_MEMORY_USAGE_TRACE), ZPL_CHECK_IF_CONF(mem_usage_trace), "ZPL_CHECK_IF_CONF(mem_usage_trace) returned an incorrect value");
}


ZPL_CODE_SCOPE_DEFINE(code_scope_enabled, 1);
ZPL_CODE_SCOPE_DEFINE(code_scope_disabled, 0);

ZTEST(zpl, test_dynamic_config_check)
{
	zassert_true(code_scope_enabled.is_enabled, "The scope should be enabled");
	zassert_false(code_scope_disabled.is_enabled, "The scope should not be enabled");
}

ZTEST(zpl, test_code_scope_macro)
{
	int counter_enabled = 0;
	int counter_disabled = 0;

	ZPL_MARK_CODE_SCOPE(code_scope_enabled) {
		counter_enabled++;
	}

	ZPL_MARK_CODE_SCOPE(code_scope_disabled) {
		counter_disabled++;
	}

	zassert_equal(1, counter_enabled, "The code scope should be ran exactly once");
	zassert_equal(1, counter_disabled, "The code scope should be ran exactly once");
}

ZTEST_SUITE(zpl, NULL, NULL, NULL, NULL, NULL);
