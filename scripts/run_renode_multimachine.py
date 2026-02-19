#!/usr/bin/env python3

# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Python script for running Zephelin profiling with multiple machines.
"""

import argparse
import time
from itertools import zip_longest
from pathlib import Path

from pyrenode3.wrappers import Emulation
from run_renode import RenodeMachine, get_renode_logger, get_renode_logs

RENODE_CLOCK_LOGIC = """
from Antmicro.Renode.Core import EmulationManager

if request.IsRead:
    emulation_time = EmulationManager.Instance.CurrentEmulation.MasterTimeSource.ElapsedVirtualTime
    request.Value = int(emulation_time.TotalMicroseconds) & 0xFFFFFFFF
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__, allow_abbrev=False)
    parser.add_argument("--debug", action="store_true", help="Enable GDB server")
    parser.add_argument(
        "--debug-start-immediately",
        action="store_true",
        help="Do not wait for input after spawning GDB server",
    )
    parser.add_argument("--sensor", type=str, help="DTS path to sensor, i.e. i2c1.lis2ds12")
    parser.add_argument("--sensor-samples", type=Path, help="Path to file with sensor samples")
    parser.add_argument("--trace-output", type=Path, help="Path to file where traces will be saved")
    parser.add_argument("--trace-output-stdout", action="store_true", help="Write trace to stdout")
    parser.add_argument(
        "--simulation-only",
        help="Only runs the simulation, without capturing the output",
        action="store_true",
    )
    parser.add_argument(
        "--timeout", type=int, help="Defines for how long the simulation should run in seconds."
    )
    parser.add_argument("--boards", type=str, nargs="+", help="List of boards to simulated")
    parser.add_argument("--elfs", type=Path, nargs="+", help="List of paths to ELF files")
    parser.add_argument(
        "--trace_uarts", type=str, nargs="+", help="List of uart names for trace collection"
    )
    parser.add_argument(
        "--console_uarts", type=str, nargs="+", help="List of uart names for conosle logs"
    )
    parser.add_argument("--repls", type=Path, nargs="+", help="List of paths to REPL files")
    parser.add_argument("--offset", type=int, help="Offset between running application (ms)")
    parser.add_argument(
        "--shared_clock_address",
        type=lambda x: int(x, 0),
        help="Hex address of shared clock, if provided all boards will \
            have access to peripheral with consistent time",
    )
    parser.add_argument("--renode-logs", action="store_true", help="Print Renode logs to stdout")
    parser.add_argument("--uart-connect", type=str, help="UART name to connect thorugh")

    args = parser.parse_args()

    emulation = Emulation()
    emulation.SyncStepping = True
    machines = []

    logger = get_renode_logger() if args.renode_logs else None

    for i, (b, e, t, c, r) in enumerate(
        zip_longest(
            args.boards,
            args.elfs,
            args.trace_uarts or [],
            args.console_uarts or [],
            args.repls or [],
            fillvalue=None,
        )
    ):
        if b is None or e is None:
            print("Amount of provided boards and ELF files must be equal")
            break
        current_repl = None
        machines.append(
            RenodeMachine(
                index=i,
                board=b,
                elf=e,
                console_uart=c,
                trace_uart=t,
                emulation=emulation,
                args=args,
                repl=r,
            )
        )

    if args.debug and not args.debug_start_immediately:
        input("Press Enter to start simulation...")
    if args.uart_connect and len(machines) == 2:
        src_mach = machines[0].mach
        dst_mach = machines[1].mach

        uart_name = args.uart_connect

        src_uart = getattr(src_mach.sysbus, uart_name)
        dst_uart = getattr(dst_mach.sysbus, uart_name)

        emulation.CreateUARTHub("hub")

        emulation.externals.hub.AttachTo(src_uart.internal)
        emulation.externals.hub.AttachTo(dst_uart.internal)

    if args.shared_clock_address:

        def setup_master_clock(machine):
            """
            Adds a peripheral at a specified address to machine, that forwards
            global emulation virtual time.
            """
            from Antmicro.Renode.Peripherals.Bus import BusPointRegistration
            from Antmicro.Renode.Peripherals.Python import PythonPeripheral

            clock_peripheral = PythonPeripheral(4, False, RENODE_CLOCK_LOGIC, None)
            machine.sysbus.Register(
                clock_peripheral, BusPointRegistration(args.shared_clock_address)
            )

        for m in machines:
            setup_master_clock(m.mach)

    if args.offset:
        from Antmicro.Renode.Time import TimeInterval

        for i in range(1, len(machines)):
            machines[i].mach.sysbus.cpu0.IsHalted = True

        offset = TimeInterval.FromMilliseconds(args.offset)
        step_time = TimeInterval.FromMilliseconds(50)

        for i in range(1, len(machines)):
            elapsed_time = 0
            while elapsed_time < offset.TotalMilliseconds:
                emulation.RunFor(step_time)
                elapsed_time += step_time.TotalMilliseconds

                for m in machines[:i]:
                    m.process_data()

            machines[i].mach.sysbus.cpu0.IsHalted = False

    print("Starting Renode simulation. Press CTRL+C to exit.")
    emulation.StartAll()
    start_time = time.time()
    try:
        while True:
            if args.simulation_only:
                time.sleep(args.timeout if args.timeout else 1)
                if args.timeout and (time.time() - start_time) > args.timeout:
                    break
                continue

            for m in machines:
                m.process_data()
            if args.timeout and (time.time() - start_time) > args.timeout:
                break
            time.sleep(0.01)

    except KeyboardInterrupt:
        pass
    finally:
        for m in machines:
            m.cleanup()
        try:
            emulation.clear()
        except Exception as e:
            # Renode might try to delete /tmp/uart-log twice and thorw an exception
            print(e)
        if logger:
            get_renode_logs(logger, 1000)

    print("\nExiting...")
