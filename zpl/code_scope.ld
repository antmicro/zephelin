/* SPDX-License-Identifier: Apache-2.0 */
/* Please keep in sync with cmake/linker_script/common/common-ram.cmake */

#include <zephyr/linker/iterable_sections.h>

ITERABLE_SECTION_RAM(zpl_code_scope_conf, Z_LINK_ITERABLE_SUBALIGN)
