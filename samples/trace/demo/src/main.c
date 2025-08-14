#include <zpl/lib.h>

#include <zephyr/drivers/sensor.h>
#include <zephyr/kernel.h>
#include <zephyr/random/random.h>
#include <generated/model_data_graph.h>
#include <generated/model_data_params.h>
#include <model.h>

#define INPUT_SHAPE_0 128
#define INPUT_SHAPE_1 3

#define OUTPUT_SHAPE_0 1
#define OUTPUT_SHAPE_1 4

static float data_buffer[INPUT_SHAPE_0][INPUT_SHAPE_1];
const struct device *const accelerometer = DEVICE_DT_GET(DT_ALIAS(accel));

/**
 * Magic Wand dataset classes
 */
const char *class_names[OUTPUT_SHAPE_1] = {"wing", "ring", "slope", "negative"};

static bool run_inference = false;

void read_accel_data(float *x, float *y, float *z);

void read_input(float *model_input);

int main(void)
{
	int status = 0;
	float __attribute((aligned(32))) model_input[INPUT_SHAPE_0][INPUT_SHAPE_1];
	float __attribute((aligned(32))) model_output[OUTPUT_SHAPE_0][OUTPUT_SHAPE_1];

	zpl_init();

	status = model_init();
	if (status) {
		printk("Model init failed %d\n", status);
		return 1;
	}

	status = model_load(model_data_graph, model_data_graph_len, model_data_params,
			    model_data_params_len);
	if (status) {
		printk("Model load failed %d\n", status);
		return 1;
	}

	for (;;) {
		read_input((float *)model_input);
		status = model_load_input((uint8_t *)model_input,
					  sizeof(float) * INPUT_SHAPE_0 * INPUT_SHAPE_1);
		if (status) {
			printk("Model load input failed %d\n", status);
			break;
		}

		if (!run_inference) {
			continue;
		}

		status = model_run();
		if (status) {
			printk("Model run failed %d\n", status);
			break;
		}

		status = model_get_output((uint8_t *)model_output);
		if (status) {
			printk("Model get output failed %d\n", status);
			break;
		}
		printk("model output: ");
		for (int i = 0; i < OUTPUT_SHAPE_1; ++i) {
			int value_int = (int)(1000 * model_output[0][i]);
			printk("%s=%d.%03d ", class_names[i], value_int / 1000, value_int % 1000);
		}
		printk("\n");
	}

	return 0;
}

void read_accel_data(float *x, float *y, float *z)
{
	struct sensor_value val[3];
	int32_t ret = 0;

	*x = 0.0f;
	*y = 0.0f;
	*z = 0.0f;

	do {
		if (!device_is_ready(accelerometer)) {
			printk("%s: not ready\n", accelerometer->name);
			break;
		}

		ret = sensor_sample_fetch(accelerometer);
		if (ret < 0 && ret != -EBADMSG) {
			printk("%s: failed to fetch sample\n", accelerometer->name);
			break;
		}

		ret = sensor_channel_get(accelerometer, SENSOR_CHAN_ACCEL_XYZ, val);
		if (ret < 0) {
			printk("%s: failed to read channel\n", accelerometer->name);
			break;
		}

		*x = sensor_value_to_float(&val[0]);
		*y = sensor_value_to_float(&val[1]);
		*z = sensor_value_to_float(&val[2]);

		printk("%s: ", accelerometer->name);
		printk("x=%+d.%03d ", (int)(*x), abs((int)((*x) * 1000)) % 1000);
		printk("y=%+d.%03d ", (int)(*y), abs((int)((*y) * 1000)) % 1000);
		printk("z=%+d.%03d\n", (int)(*z), abs((int)((*z) * 1000)) % 1000);
	} while (0);
}

void read_input(float *model_input)
{
	static int sample_idx = 0;
	float x, y, z;
	int input_offset;

	read_accel_data(&x, &y, &z);

	/* convert to mili G */
	data_buffer[sample_idx][0] = 1000.0f * x;
	data_buffer[sample_idx][1] = 1000.0f * y;
	data_buffer[sample_idx][2] = 1000.0f * z;

	++sample_idx;
	sample_idx %= INPUT_SHAPE_0;

	/* run inference every 16 samples */
	run_inference = (sample_idx % 16) == 0;

	input_offset = sample_idx * INPUT_SHAPE_1;

	memcpy(model_input, &data_buffer[sample_idx][0],
	       (INPUT_SHAPE_0 - sample_idx) * sizeof(float) * INPUT_SHAPE_1);
	if (sample_idx > 0) {
		memcpy(&model_input[(INPUT_SHAPE_0 - sample_idx) * INPUT_SHAPE_1], data_buffer,
		       sample_idx * sizeof(float) * INPUT_SHAPE_1);
	}
}
