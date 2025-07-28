#include <zephyr/kernel.h>
#include <zpl/lib.h>

ZPL_CODE_SCOPE_DEFINE(code_scope1, 0);
ZPL_CODE_SCOPE_DEFINE(code_scope2, 0);
ZPL_CODE_SCOPE_DEFINE(code_scope3, 1);
ZPL_CODE_SCOPE_DEFINE(code_scope4, 1);

void test_function(int counter)
{
	printk("Test: %d\n", counter);
	ZPL_MARK_CODE_SCOPE(code_scope1) {
		printk("Inner test: %d\n", counter);
		k_sleep(K_MSEC(100));
	}
}

void test_function2(int counter)
{
	zpl_code_scope_enter(code_scope2);

		printk("Inside of scope test_function2 %d\n", counter);
		k_sleep(K_MSEC(100));

	zpl_code_scope_exit(code_scope2);
}

void test_recurrent(int counter)
{
	printk("Recurrent: %d\n", counter);
	ZPL_MARK_CODE_SCOPE(code_scope4) {
		k_sleep(K_MSEC(100));
		if (counter == 0) return;
		test_recurrent(counter - 1);
	}
}

int main(void)
{
	zpl_init();
	k_sleep(K_MSEC(1000));
	for (int i = 0; i < 10; i++) {
		ZPL_MARK_CODE_SCOPE(code_scope3) {
			test_function(i);
		}
		k_sleep(K_MSEC(100));
	}

	for (int i = 0; i < 5; i++) {
		test_function2(i);
		k_sleep(K_MSEC(100));
	}

	test_recurrent(5);

	return 0;
}
