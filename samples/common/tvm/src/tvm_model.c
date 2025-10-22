/*
 * Copyright (c) 2025 Analog Devices, Inc.
 * Copyright (c) 2025 Antmicro <www.antmicro.com>
 *
 * SPDX-License-Identifier: Apache-2.0
 */


#include <tvm/runtime/c_backend_api.h>
#include <tvm/runtime/crt/crt.h>
#include <tvm/runtime/crt/graph_executor.h>
#include <tvm/runtime/crt/internal/graph_executor/graph_executor.h>
#include <dlpack/dlpack.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <zpl/tvm_profiler.h>
#include <zpl/inference_event.h>
#include <tvm/runtime/crt/module.h>
#include "tvm_model.h"
#include "magic_wand.h"

static const DLDevice g_device = {kDLCPU, 1};
static TVMGraphExecutor *gp_tvm_graph_executor;
static TVMModuleHandle g_tvm_module_handle;

int model_init(void)
{
	gp_tvm_graph_executor = NULL;
	return TVMInitializeRuntime();
}

int model_load(const uint8_t *model_graph, uint32_t model_graph_size, const uint8_t *model_params, uint32_t model_params_size, TVMGraphExecutor **tvm_graph_executor, TVMModuleHandle *tvm_module_handle, const TVMModule *tvm_module)
{
	int status = 0;

	if (tvm_graph_executor == NULL) {
		tvm_graph_executor = &gp_tvm_graph_executor;
	}
	if (tvm_module_handle == NULL) {
		tvm_module_handle = &g_tvm_module_handle;
	}
	if (tvm_module == NULL) {
		tvm_module = TVMSystemLibEntryPoint();
	}

	do {
		status = TVMModCreateFromCModule(tvm_module, tvm_module_handle);
		if (status) {
				printk("CreateFromCModule\n");
		    break;
		}

		status = TVMGraphExecutor_Create(model_graph, *tvm_module_handle, &g_device,
													 tvm_graph_executor);
		if (status) {
				printk("GraphExecutor_Create\n");
		    break;
		}

		status = TVMGraphExecutor_LoadParams(*tvm_graph_executor, model_params,
														 model_params_size);
		if (status) {
				printk("GraphExecutor_LoadParams\n");
		    break;
		}
	} while (0);

	return status;
}

int model_load_input(const uint8_t *input, uint32_t input_size, TVMGraphExecutor *tvm_graph_executor, bool quantized)
{
	if (tvm_graph_executor == NULL) {
		tvm_graph_executor = gp_tvm_graph_executor;
	}

	DLTensor tensor_in;

	tensor_in.device = g_device;
	if (quantized) {
		tensor_in.ndim = 2;
		tensor_in.dtype.code = kDLInt;
		tensor_in.dtype.bits = 8;
		uint64_t shape[2] = {1, 1};
		tensor_in.shape = shape;
	} else {
		tensor_in.ndim = 4;
		tensor_in.dtype.code = kDLFloat;
		tensor_in.dtype.bits = 32;
		uint64_t shape[4] = {1, 128, 3, 1};
		tensor_in.shape = shape;
	}
	tensor_in.dtype.lanes = 0;
	tensor_in.strides = NULL;
	tensor_in.byte_offset = 0;

	tensor_in.data = (void *)input;

	/* TVM does not allow setting input by index, so we need to retrieve its name */
	uint32_t input_node_id = tvm_graph_executor->input_nodes[0];
	char *input_name = tvm_graph_executor->nodes[input_node_id].name;

	TVMGraphExecutor_SetInput(tvm_graph_executor, input_name, &tensor_in);
	return 0;
}

int model_run(TVMGraphExecutor *tvm_graph_executor)
{
	if (tvm_graph_executor == NULL) {
		tvm_graph_executor = gp_tvm_graph_executor;
	}

	TVMGraphExecutor_Run(tvm_graph_executor);
	return 0;
}

int model_get_output(uint8_t *output, TVMGraphExecutor *tvm_graph_executor, bool quantized)
{
	if (tvm_graph_executor == NULL) {
		tvm_graph_executor = gp_tvm_graph_executor;
	}

	int tvm_status = 0;
	DLTensor tensor_out;

	tensor_out.device = g_device;
	tensor_out.ndim = 2;
	uint64_t shape[2] = {1, 4};
	if (quantized) {
		tensor_out.dtype.code = kDLInt;
		tensor_out.dtype.bits = 8;
		shape[1] = 1;
	} else {
		tensor_out.dtype.code = kDLFloat;
		tensor_out.dtype.bits = 32;
	}
	tensor_out.shape = shape;
	tensor_out.dtype.lanes = 0;
	tensor_out.strides = NULL;
	tensor_out.byte_offset = 0;

	tensor_out.data = (void *)output;

	tvm_status = TVMGraphExecutor_GetOutput(tvm_graph_executor, 0, &tensor_out);

	return tvm_status;
}
