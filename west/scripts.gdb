# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
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
