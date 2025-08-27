#include <zpl/lib.h>
#include <zpl/tflm_events.h>
#include <zephyr/kernel.h>
#include <stdio.h>

int main(void)
{
	const char *tflm_op_tag = "TFLM_OP";

	zpl_init();

	zpl_emit_tflm_enter_event(k_cycle_get_32(), 0, 0, tflm_op_tag, 0, 1);
	zpl_emit_tflm_exit_event(k_cycle_get_32(), 0, 0, tflm_op_tag, 2, 3);

	return 0;
}
