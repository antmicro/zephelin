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
#include <zpl/tvm_profiler.h>
#include <zpl/inference_event.h>
#include "model.h"
#include "magic_wand.h"

extern TVMProfiler tvm_profiler;

static const DLDevice g_device = {kDLCPU, 1};
static TVMGraphExecutor *gp_tvm_graph_executor = NULL;
static TVMModuleHandle g_tvm_module_handle;

int model_init(void)
{
	return TVMInitializeRuntime();
}

int model_load(const uint8_t *model_graph, uint32_t model_graph_size, const uint8_t *model_params, uint32_t model_params_size)
{
	int status = 0;

	do {
		const TVMModule *tvm_module = TVMSystemLibEntryPoint();
		if (NULL == tvm_module)
		{
		    status = 1;
		    break;
		}

		status = TVMModCreateFromCModule(tvm_module, &g_tvm_module_handle);
		if (status){
		    break;
		}

		status = TVMGraphExecutor_Create(model_graph, g_tvm_module_handle, &g_device,
		                                 &gp_tvm_graph_executor);
		if (status){
		    break;
		}

		status = TVMGraphExecutor_LoadParams(gp_tvm_graph_executor, model_params,
		                                     model_params_size);
		if (status){
		    break;
		}
	} while(0);

	return status;
}

int model_load_input(const uint8_t *input, uint32_t input_size)
{
	DLTensor tensor_in;

	tensor_in.device = g_device;
	tensor_in.ndim = 4;
	tensor_in.dtype.code = kDLFloat;
	tensor_in.dtype.bits = 32;
	tensor_in.dtype.lanes = 0;
	uint64_t shape[4] = {1, 128, 3, 1};
	tensor_in.shape = shape;
	tensor_in.strides = NULL;
	tensor_in.byte_offset = 0;

	tensor_in.data = (void *)input;

	// TVM does not allow setting input by index, so we need to retrieve its name
	uint32_t input_node_id = gp_tvm_graph_executor->input_nodes[0];
	char *input_name = gp_tvm_graph_executor->nodes[input_node_id].name;

	TVMGraphExecutor_SetInput(gp_tvm_graph_executor, input_name, &tensor_in);
	return 0;
}

int model_run(void)
{
	zpl_inference_enter();
	TVMGraphExecutor_Run(gp_tvm_graph_executor, &tvm_profiler);
	zpl_inference_exit();

	zpl_tvm_profiler_dump_events();
	return 0;
}

int model_get_output(uint8_t *output)
{
	int tvm_status = 0;
	DLTensor tensor_out;

	tensor_out.device = g_device;
	tensor_out.ndim = 2;
	tensor_out.dtype.code = kDLFloat;
	tensor_out.dtype.bits = 32;
	tensor_out.dtype.lanes = 0;
	uint64_t shape[2] = {1, 4};
	tensor_out.shape = shape;
	tensor_out.strides = NULL;
	tensor_out.byte_offset = 0;

	tensor_out.data = (void *)output;

	tvm_status = TVMGraphExecutor_GetOutput(gp_tvm_graph_executor, 0, &tensor_out);

	return tvm_status;
}
