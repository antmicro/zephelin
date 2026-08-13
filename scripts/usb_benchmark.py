#!/usr/bin/env python3

# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Pure USB sink for Zephelin tracing — captures bulk-IN data and reports
real-time throughput (bytes/s, events/s) without parsing CTF payloads.

Usage:
    python usb_sink.py --vid 0xXXXX --pid 0xYYYY [--output trace.bin] [--duration SEC]

Dependencies: pyusb (pip install pyusb)
"""

import argparse
import signal
import sys
import threading
import time

import usb.core
import usb.util

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CTF_START_TAG = b"_zpl_ctf_start__"
DEFAULT_TIMEOUT_MS = 1000  # USB read timeout
REPORT_INTERVAL = 1.0  # seconds between throughput reports
BUFSIZE = 64 * 1024  # 64 KB read buffer


# ---------------------------------------------------------------------------
# Throughput tracker
# ---------------------------------------------------------------------------
class ThroughputTracker:
    """Sliding-window bytes-per-second counter."""

    def __init__(self, interval: float = REPORT_INTERVAL):
        """Initialize tracker with given report interval."""
        self.interval = interval
        self.total_bytes = 0
        self.total_events = 0
        self.start_time = time.monotonic()
        self.last_report = self.start_time
        self.window_bytes = 0
        self.window_start = self.start_time
        self.last_bytes = 0
        self.last_events = 0
        self.reads = 0

    def record(self, n_bytes: int, n_events: int = 0):
        now = time.monotonic()
        self.total_bytes += n_bytes
        self.total_events += n_events
        self.reads += 1

        # Update sliding window
        if now - self.window_start >= self.interval:
            self.window_bytes = n_bytes
            self.window_start = now

    def report(self, csv_fh=None):
        now = time.monotonic()
        elapsed = now - self.start_time
        if elapsed <= 0:
            return

        overall_bps = self.total_bytes / elapsed

        # Instantaneous rate (since last report)
        dt = now - self.last_report
        instant_bps = 0
        instant_eps = 0
        if dt > 0:
            instant_bps = (self.total_bytes - self.last_bytes) / dt
            if self.total_events > self.last_events:
                instant_eps = (self.total_events - self.last_events) / dt

        self.last_report = now
        self.last_bytes = self.total_bytes
        self.last_events = self.total_events

        # Format throughput
        def fmt_bps(bps):
            if bps >= 1_000_000:
                return f"{bps / 1_000_000:.2f} MB/s"
            elif bps >= 1_000:
                return f"{bps / 1_000:.2f} kB/s"
            else:
                return f"{bps:.0f} B/s"

        line = (
            f"  elapsed={elapsed:6.1f}s  "
            f"reads={self.reads:6d}  "
            f"total={self.total_bytes / 1024:8.1f} kB  "
            f"overall={fmt_bps(overall_bps):>10s}  "
            f"instant={fmt_bps(instant_bps):>10s}"
        )
        if self.total_events:
            line += f"  events={self.total_events:>8d}  eps={instant_eps:.1f}"

        print(line, end="\r")

        if csv_fh:
            csv_fh.write(
                f"{elapsed:.3f},{self.total_bytes},{overall_bps},{instant_bps},{self.total_events},{instant_eps}\n"
            )
            csv_fh.flush()


# ---------------------------------------------------------------------------
# USB capture loop
# ---------------------------------------------------------------------------
def capture(
    vid: int, pid: int, output_path: str | None, duration: int | None, csv_file: str | None = None
):
    """Capture from USB IN endpoint and report throughput."""
    tracker = ThroughputTracker()
    stop_event = threading.Event()

    def _sigint(signum, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, _sigint)

    print(f"Looking for USB device vid=0x{vid:04x} pid=0x{pid:04x}...")

    dev = usb.core.find(idVendor=vid, idProduct=pid)
    if dev is None:
        print("ERROR: device not found")
        sys.exit(1)

    print(f"Found {dev.manufacturer} {dev.product} (serial={dev.serial_number})")
    print("Claiming interface and starting capture...")
    print("-" * 80)

    if dev.get_active_configuration() is None:
        dev.set_configuration()
    cfg = dev.get_active_configuration()
    intf = cfg[(0, 0)]
    usb.util.claim_interface(dev, intf)

    # Find IN endpoint (bulk)
    read_ep = usb.util.find_descriptor(
        intf,
        custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
        == usb.util.ENDPOINT_IN,
    )
    if read_ep is None:
        print("ERROR: no IN endpoint found")
        sys.exit(1)

    # Find OUT endpoint and send enable command
    write_ep = usb.util.find_descriptor(
        intf,
        custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
        == usb.util.ENDPOINT_OUT,
    )
    if write_ep:
        write_ep.write(b"enable")

    buf = usb.util.create_buffer(BUFSIZE)
    start_time = time.monotonic()

    # Open CSV file once
    csv_fh = None
    if csv_file:
        csv_fh = open(csv_file, "a")

    try:
        while not stop_event.is_set():
            # Check if duration has expired
            if duration:
                elapsed = time.monotonic() - start_time
                if elapsed >= duration:
                    break
                remaining = int((duration - elapsed) * 1000)
            else:
                remaining = None

            timeout = remaining if remaining is not None else DEFAULT_TIMEOUT_MS

            try:
                n = read_ep.read(buf, timeout)
            except usb.core.USBTimeoutError:
                # Timeout with no data — just continue
                continue

            if n == 0:
                continue

            # Detect CTF start tag for event counting
            events = 0
            if tracker.total_events == 0 and CTF_START_TAG in buf[:n]:
                events = 1
                tracker.total_events = 1
                tracker.last_events = 1

            tracker.record(n, events)

            # Write to file if requested
            if output_path:
                with open(output_path, "ab") as f:
                    f.write(buf[:n])

            # Report throughput on timer (not every read)
            if time.monotonic() - tracker.last_report >= REPORT_INTERVAL:
                tracker.report(csv_fh)

    except KeyboardInterrupt:
        pass
    finally:
        if csv_fh:
            csv_fh.close()
        usb.util.release_interface(dev, intf)

    # Final summary
    print("-" * 80)
    tracker.report()
    elapsed = time.monotonic() - start_time
    print(
        f"\nDone. Captured {tracker.total_bytes:,} bytes in {elapsed:.1f}s "
        f"({tracker.total_bytes / elapsed / 1000:.2f} kB/s avg)"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    """Parse args and run capture."""
    parser = argparse.ArgumentParser(
        description="USB sink for Zephelin tracing — captures and reports throughput",
        allow_abbrev=False,
    )
    parser.add_argument("--vid", required=True, help="USB vendor ID (hex, e.g. 0x1234)")
    parser.add_argument("--pid", required=True, help="USB product ID (hex, e.g. 0x5678)")
    parser.add_argument("-o", "--output", help="Output file path (binary)")
    parser.add_argument(
        "-d", "--duration", type=int, help="Capture duration in seconds (0=forever)"
    )
    parser.add_argument("--stats-file", help="Write CSV stats to file")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-interval reports")

    args = parser.parse_args()

    vid = int(args.vid, 16)
    pid = int(args.pid, 16)

    csv_file = None
    if args.stats_file:
        csv_file = args.stats_file
        with open(csv_file, "w") as f:
            f.write("elapsed,total_bytes,overall_bps,instant_bps,total_events,instant_eps\n")

    capture(vid, pid, args.output, args.duration, csv_file)


if __name__ == "__main__":
    main()
