# Copyright (c) 2025 Analog Devices, Inc.
# Copyright (c) 2025 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides Robot Framework keywords for instrumentation testing.
"""

import subprocess


def check_instrumentation_enabled_status(instrumentation_script, pty_link):
    """
    Checks instrumentation status.

    Parameters
    ----------
    instrumentation_script : str
        Path to instrumentation script.
    pty_link : str
        Pty path, can also be a TCP/IP port.
    """
    proc = subprocess.Popen(
        [instrumentation_script, "--serial", pty_link, "status"], stdout=subprocess.PIPE
    )
    (output, _) = proc.communicate()
    exit_code = proc.wait()
    if exit_code != 0:
        raise Exception("Failed to get instrumentation status: {}.".format(output))
    if "Trace supported" not in output.decode("utf-8"):
        raise Exception("Instrumentation callgraph mode is not enabled")


def set_instrumentation_coupled_trigger(instrumentation_script, pty_link, trigger_function):
    """
    Set instrumentation function trigger.

    Parameters
    ----------
    instrumentation_script : str
        Path to instrumentation script.
    pty_link : str
        Pty path, can also be a TCP/IP port.
    trigger_function: str
        Name of the trigger function.
    """
    proc = subprocess.Popen(
        [instrumentation_script, "--serial", pty_link, "trace", "-c", trigger_function],
        stdout=subprocess.PIPE,
    )
    (output, _) = proc.communicate()
    exit_code = proc.wait()
    if exit_code != 0:
        raise Exception("Failed to set coupled trigger: {}.".format(output))


def trigger_instrumentation_reboot(instrumentation_script, pty_link):
    """
    Reboot instrumentation.

    Parameters
    ----------
    instrumentation_script : str
        Path to instrumentation script.
    pty_link : str
        Pty path, can also be a TCP/IP port.
    """
    proc = subprocess.Popen(
        [instrumentation_script, "--serial", pty_link, "reboot"], stdout=subprocess.PIPE
    )
    (output, _) = proc.communicate()
    exit_code = proc.wait()
    if exit_code != 0:
        raise Exception("Failed to reboot target: {}.".format(output))


def generate_instrumentation_callgraph(instrumentation_script, pty_link):
    """
    Generate instrumentation callgraph.

    Parameters
    ----------
    instrumentation_script : str
        Path to instrumentation script.
    pty_link : str
        Pty path, can also be a TCP/IP port.
    """
    proc = subprocess.Popen(
        [instrumentation_script, "--serial", pty_link, "trace"], stdout=subprocess.PIPE
    )
    (output, _) = proc.communicate()
    exit_code = proc.wait()
    if exit_code != 0:
        raise Exception("Failed to reboot target: {}.".format(output))
    with open("callgraph.txt", "wb") as f:
        f.write(output)


def generate_instrumentation_perfetto_trace(instrumentation_script, pty_link):
    """
    Generate perfetto trace.

    Parameters
    ----------
    instrumentation_script : str
        Path to instrumentation script.
    pty_link : str
        Pty path, can also be a TCP/IP port.
    """
    proc = subprocess.Popen(
        [
            instrumentation_script,
            "--serial",
            pty_link,
            "trace",
            "--perfetto",
            "--output",
            "zephyr_trace.json",
        ],
        stdout=subprocess.PIPE,
    )
    (output, _) = proc.communicate()
    exit_code = proc.wait()
    if exit_code != 0:
        raise Exception("Failed to reboot target: {}.".format(output))
    with open("callgraph.txt", "wb") as f:
        f.write(output)
