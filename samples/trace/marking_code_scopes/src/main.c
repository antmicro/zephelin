#include <zephyr/kernel.h>
#include <zpl/lib.h>

ZPL_CODE_SCOPE_DEFINE(code_scope1, 0);
ZPL_CODE_SCOPE_DEFINE(code_scope2, 0);
ZPL_CODE_SCOPE_DEFINE(code_scope3, 1);

void test_function(int counter)
{
	printf("Test: %d\n", counter);
	ZPL_MARK_CODE_SCOPE(code_scope1) {
		printf("Inner test: %d\n", counter);
	}
}

void test_function2(int counter)
{
	zpl_code_scope_enter(code_scope2);

	printf("Inside of scope test_function2 %d\n", counter);

	zpl_code_scope_exit(code_scope2);
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

	return 0;
}
