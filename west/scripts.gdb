# Copyright (c) 2025-2026 Analog Devices, Inc.
# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

# Helper scripts for west zpl-gdb-capture command

set pagination off

define wait_buffer_full
	rwatch buffer_full if buffer_full
	if !buffer_full
		continue
	end
end

define wait_n_bytes
	rwatch pos if pos >= $arg0
	if pos < $arg0
		continue
	end
end

define calculate_start_end
	set $start = &ram_tracing
	set $end = (char*)&ram_tracing + pos
end

define strcmp
	python print cmp(gdb.execute("output $arg0", to_string=True).strip('"'), $arg1)
end

# $arg0 : Path to the file
# $arg1 : The size of buffer
# $arg2 : Path to the log file
define dump_data_to_file
	break tracing_backend_ram_output if (pos + length) > $arg1
	set $append = 0
	set $measure_time = !$_streq("$arg2", "/dev/null")
	if $measure_time
		set logging file $arg2
		set logging on
		python import time
	end
	while (1)
		continue
		if $measure_time
			python starttime = time.time()
		end
		calculate_start_end
		if $append
			append binary memory $arg0 $start $end
		else
			dump binary memory $arg0 $start $end
		end
		call tracing_backend_ram_init()
		set $append = 1
		if $measure_time
			python print ("save_time:", time.time() - starttime)
			print $start
			print $end
		end
	end
end
