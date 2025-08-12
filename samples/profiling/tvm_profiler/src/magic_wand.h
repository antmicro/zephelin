#ifndef SAMPLES_TRACE_TVM_PROFILER_SRC_MAGIC_WAND_H_
#define SAMPLES_TRACE_TVM_PROFILER_SRC_MAGIC_WAND_H_

#include <tvm/runtime/crt/module.h>
#include <tvm/runtime/crt/packed_func.h>

#define TVMGEN_FUNCTIONS(FUNC)                         \
    FUNC(tvmgen_default_fused_nn_batch_flatten)        \
    FUNC(tvmgen_default_fused_nn_conv2d_add_nn_relu)   \
    FUNC(tvmgen_default_fused_nn_conv2d_add_nn_relu_1) \
    FUNC(tvmgen_default_fused_nn_dense_add)            \
    FUNC(tvmgen_default_fused_nn_dense_add_nn_relu)    \
    FUNC(tvmgen_default_fused_nn_max_pool2d)           \
    FUNC(tvmgen_default_fused_nn_max_pool2d_1)         \
    FUNC(tvmgen_default_fused_nn_softmax)

#define TVMGEN_FUNCTIONS_COUNT "\x08"

#define TVMGEN_DECLARE(func_name)                                                                      \
    extern int32_t func_name(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value, \
                             int32_t *out_ret_tcode, void *resource_handle);

#define TVMGEN_FUNC_ARRAY(func_name) (TVMBackendPackedCFunc) func_name,

#define TVMGEN_FUNC_REGISTRY(func_name) "\0" #func_name

TVMGEN_FUNCTIONS(TVMGEN_DECLARE);

const TVMBackendPackedCFunc tvm_func_array[] = {TVMGEN_FUNCTIONS(TVMGEN_FUNC_ARRAY)};

const TVMFuncRegistry tvm_func_reg = {.names = TVMGEN_FUNCTIONS_COUNT TVMGEN_FUNCTIONS(TVMGEN_FUNC_REGISTRY) "\0",
                                      .funcs = tvm_func_array};

const TVMModule g_tvm_module = {&tvm_func_reg};

const TVMModule *TVMSystemLibEntryPoint(void) { return &g_tvm_module; }

#endif // SAMPLES_TRACE_TVM_PROFILER_SRC_MAGIC_WAND_H_
