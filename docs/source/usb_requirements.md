# Trace capture USB interface requirements

This chapter describes the requirements to enable trace capture via the
Zephelin's USB interface. Zephelin provides an out-of-the box USB device
implementation in `zpl/backends/usb_backend.c`

To enable the USB interface, the user y-should select
the `CONFIG_ZPL_TRACE_BACKEND_USB` Kconfig option. The
`CONFIG_ZPL_TRACE_BACKEND_USB` option automatically selects every necessary
software component in Zephyr required to run the USB device stack.

## Driver requirements

A USB device driver needs to be provided for the given platform when the
USB trace capture interface is used. Make sure there is a UDC driver available
for your platform upstream (in `drivers/usb/udc/`), or provide your own UDC
driver implementation as described in the
[Zephyr documentation](https://docs.zephyrproject.org/latest/connectivity/usb/device_next/api/udc.html).

## Devicetree requirements

The USB device implemented by Zephelin expects the `zephyr_udc0` node to be
present in the devicetree file. Make sure the platform devicetree file provides
a valid `chosen` node with the `zephyr_udc0` property defined. The property
under `/chosen/zephyr_udc0` should point to a platform USB controller node.
