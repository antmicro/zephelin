#include <zpl/die_temp.h>

#include <stdio.h>
#include <math.h>
#include <zephyr/kernel.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/tracing/tracing_format.h>

#define SENSORS_COUNT CONFIG_ZPL_DIE_TEMP_PROFILING_SENSORS_COUNT

#define DIE_TEMP_ALIAS(i) DT_ALIAS(_CONCAT(die_temp, i))
#define DIE_TEMPERATURE_SENSOR(i, _)                                                               \
	IF_ENABLED(DT_NODE_EXISTS(DIE_TEMP_ALIAS(i)), (DEVICE_DT_GET(DIE_TEMP_ALIAS(i)),))

static const struct device *const sensors[] = {LISTIFY(SENSORS_COUNT, DIE_TEMPERATURE_SENSOR, ())};

void zpl_emit_die_temp_event(void)
{
	struct sensor_value val;
	int rc = 0;
	float die_temp[SENSORS_COUNT];

	for (int i = 0; i < SENSORS_COUNT; ++i) {
		if (i >= ARRAY_SIZE(sensors)) {
			die_temp[i] = NAN;
			continue;
		}
		if (!device_is_ready(sensors[i])){
			die_temp[i] = NAN;
			continue;
		}
		/* fetch sensor samples */
		rc = sensor_sample_fetch(sensors[i]);
		if (rc) {
			die_temp[i] = NAN;
			continue;
		}
		/* get sensor channel value */
		rc = sensor_channel_get(sensors[i], SENSOR_CHAN_DIE_TEMP, &val);
		if (rc) {
			die_temp[i] = NAN;
			continue;
		}
		die_temp[i] = sensor_value_to_float(&val);
	}

#if defined(CONFIG_ZPL_TRACE_FORMAT_CTF)
	zpl_die_temp_event_t zpl_die_temp_event = {
		.timestamp = k_cyc_to_ns_floor64(k_cycle_get_32()),
		.id = ZPL_DIE_TEMP_EVENT,
		.sensor_count = SENSORS_COUNT,
	};
	for (int i = 0; i < SENSORS_COUNT; ++i) {
		zpl_die_temp_event.die_temp[i] = die_temp[i];
	}
	tracing_format_raw_data((uint8_t *)&zpl_die_temp_event, sizeof(zpl_die_temp_event_t));
#elif defined(CONFIG_ZPL_TRACE_FORMAT_PLAINTEXT)
#define APPEND_TO_STR(str_, str_p_, fmt_, ...) \
	snprintf(str_p_, MAX(0, sizeof(str_) - (int)(str_p_ - str_)), fmt_ __VA_OPT__(,) __VA_ARGS__);

	char trace_str[24 + 20 * SENSORS_COUNT];
	char *trace_str_p = trace_str;
	memset(trace_str, 0, sizeof(trace_str));

	trace_str_p += APPEND_TO_STR(trace_str, trace_str_p, "zpl_die_temp_event:");
	for (int i = 0; i < SENSORS_COUNT; ++i) {
		if (isnan(die_temp[i])) {
			trace_str_p += APPEND_TO_STR(trace_str, trace_str_p, " die_temp[%d]=NaN", i);
		} else {
			int die_temp_int = (int)(100*die_temp[i]);
			trace_str_p += APPEND_TO_STR(trace_str, trace_str_p, " die_temp[%d]=%d.%d", i, die_temp_int / 100, die_temp_int % 100);
		}
	}
	trace_str_p += APPEND_TO_STR(trace_str, trace_str_p, "\n");
	TRACING_STRING("%s", trace_str);
#undef APPEND_TO_STR
#endif /* CONFIG_ZPL_TRACE_FORMAT_* */
}

#ifdef CONFIG_ZPL_DIE_TEMP_TRACE

static void zpl_profile_die_temp(void)
{
	while (true) {
		zpl_emit_die_temp_event();
		k_msleep(CONFIG_ZPL_DIE_TEMP_PROFILING_INTERVAL);
	}
}

K_THREAD_DEFINE(zpl_die_temp_profiling,
				CONFIG_ZPL_DIE_TEMP_PROFILING_THREAD_STACK_SIZE,
				zpl_profile_die_temp, NULL, NULL, NULL,
				CONFIG_ZPL_DIE_TEMP_PROFILING_THREAD_PRIORITY,
				0, CONFIG_ZPL_DIE_TEMP_PROFILING_THREAD_DELAY);

#endif /* CONFIG_ZPL_DIE_TEMP_TRACE */
