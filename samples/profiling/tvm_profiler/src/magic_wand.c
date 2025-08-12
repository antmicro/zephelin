// tvm target: c -keys=arm_cpu,cpu -device=arm_cpu -march=armv7e-m -mcpu=cortex-m7 -model=stm32f746xx
#define TVM_EXPORTS
#include "tvm/runtime/c_runtime_api.h"
#include <math.h>
#include <stdbool.h>
#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_batch_flatten(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
                                          int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_conv2d_add_nn_relu(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
                                               int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_conv2d_add_nn_relu_1(void *args, int32_t *arg_type_ids, int32_t num_args,
                                                 void *out_ret_value, int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_dense_add(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
                                      int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_dense_add_nn_relu(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
                                              int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_max_pool2d(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
                                       int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_max_pool2d_1(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
                                         int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_softmax(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
                                    int32_t *out_ret_tcode, void *resource_handle);
#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL float
    expf(float);
#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_batch_flatten(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
                                          int32_t *out_ret_tcode, void *resource_handle)
{
    void *p0 = (((TVMValue *)args)[0].v_handle);
    void *tensor = (((TVMValue *)args)[1].v_handle);
    void *p0_1 = (((DLTensor *)p0)[0].data);
    void *tvmgen_default_fused_nn_batch_flatten_p0_strides = (((DLTensor *)p0)[0].strides);
    void *tensor_1 = (((DLTensor *)tensor)[0].data);
    void *tvmgen_default_fused_nn_batch_flatten_tensor_strides = (((DLTensor *)tensor)[0].strides);
    if (!(tvmgen_default_fused_nn_batch_flatten_p0_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_batch_flatten_tensor_strides == NULL))
    {
    }
    for (int32_t ax1_outer = 0; ax1_outer < 56; ++ax1_outer)
    {
        for (int32_t ax1_inner = 0; ax1_inner < 4; ++ax1_inner)
        {
            int32_t cse_var_1 = ((ax1_outer * 4) + ax1_inner);
            ((float *)tensor_1)[cse_var_1] = ((float *)p0_1)[cse_var_1];
        }
    }
    return 0;
}

#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_conv2d_add_nn_relu(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
                                               int32_t *out_ret_tcode, void *resource_handle)
{
    void *p0 = (((TVMValue *)args)[0].v_handle);
    void *p1 = (((TVMValue *)args)[1].v_handle);
    void *p2 = (((TVMValue *)args)[2].v_handle);
    void *T_relu = (((TVMValue *)args)[3].v_handle);
    void *p0_1 = (((DLTensor *)p0)[0].data);
    void *tvmgen_default_fused_nn_conv2d_add_nn_relu_p0_strides = (((DLTensor *)p0)[0].strides);
    void *p1_1 = (((DLTensor *)p1)[0].data);
    void *tvmgen_default_fused_nn_conv2d_add_nn_relu_p1_strides = (((DLTensor *)p1)[0].strides);
    void *p2_1 = (((DLTensor *)p2)[0].data);
    void *tvmgen_default_fused_nn_conv2d_add_nn_relu_p2_strides = (((DLTensor *)p2)[0].strides);
    void *T_relu_1 = (((DLTensor *)T_relu)[0].data);
    void *tvmgen_default_fused_nn_conv2d_add_nn_relu_T_relu_strides = (((DLTensor *)T_relu)[0].strides);
    if (!(tvmgen_default_fused_nn_conv2d_add_nn_relu_p0_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_conv2d_add_nn_relu_p1_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_conv2d_add_nn_relu_p2_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_conv2d_add_nn_relu_T_relu_strides == NULL))
    {
    }
    for (int32_t ax0_ax1_outer_fused = 0; ax0_ax1_outer_fused < 128; ++ax0_ax1_outer_fused)
    {
        float PadInput[12];
        float conv[8];
        for (int32_t ax2_outer = 0; ax2_outer < 3; ++ax2_outer)
        {
            for (int32_t i1 = 0; i1 < 4; ++i1)
            {
                for (int32_t i2 = 0; i2 < 3; ++i2)
                {
                    int32_t cse_var_3 = (i1 + ax0_ax1_outer_fused);
                    int32_t cse_var_2 = (i2 + ax2_outer);
                    int32_t cse_var_1 = (i1 * 3);
                    PadInput[(cse_var_1 + i2)] =
                        (((((1 <= cse_var_3) && (cse_var_3 < 129)) && (1 <= cse_var_2)) && (cse_var_2 < 4))
                             ? ((float *)p0_1)[((((cse_var_1 + (ax0_ax1_outer_fused * 3)) + i2) + ax2_outer) - 4)]
                             : 0.000000e+00f);
                }
            }
            for (int32_t oci_init = 0; oci_init < 8; ++oci_init)
            {
                conv[oci_init] = 0.000000e+00f;
            }
            for (int32_t kh = 0; kh < 4; ++kh)
            {
                for (int32_t kw = 0; kw < 3; ++kw)
                {
                    for (int32_t oci = 0; oci < 8; ++oci)
                    {
                        conv[oci] =
                            (conv[oci] + (PadInput[((kh * 3) + kw)] * ((float *)p1_1)[(((kh * 24) + (kw * 8)) + oci)]));
                    }
                }
            }
            for (int32_t ax3_inner = 0; ax3_inner < 8; ++ax3_inner)
            {
                float v_ = conv[ax3_inner] + ((float *)p2_1)[ax3_inner];
                ((float *)T_relu_1)[(((ax0_ax1_outer_fused * 24) + (ax2_outer * 8)) + ax3_inner)] =
                    ((v_) > (0.000000e+00f) ? (v_) : (0.000000e+00f));
            }
        }
    }
    return 0;
}

#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_conv2d_add_nn_relu_1(void *args, int32_t *arg_type_ids, int32_t num_args,
                                                 void *out_ret_value, int32_t *out_ret_tcode, void *resource_handle)
{
    void *p0 = (((TVMValue *)args)[0].v_handle);
    void *p1 = (((TVMValue *)args)[1].v_handle);
    void *p2 = (((TVMValue *)args)[2].v_handle);
    void *T_relu = (((TVMValue *)args)[3].v_handle);
    void *p0_1 = (((DLTensor *)p0)[0].data);
    void *tvmgen_default_fused_nn_conv2d_add_nn_relu_1_p0_strides = (((DLTensor *)p0)[0].strides);
    void *p1_1 = (((DLTensor *)p1)[0].data);
    void *tvmgen_default_fused_nn_conv2d_add_nn_relu_1_p1_strides = (((DLTensor *)p1)[0].strides);
    void *p2_1 = (((DLTensor *)p2)[0].data);
    void *tvmgen_default_fused_nn_conv2d_add_nn_relu_1_p2_strides = (((DLTensor *)p2)[0].strides);
    void *T_relu_1 = (((DLTensor *)T_relu)[0].data);
    void *tvmgen_default_fused_nn_conv2d_add_nn_relu_1_T_relu_strides = (((DLTensor *)T_relu)[0].strides);
    if (!(tvmgen_default_fused_nn_conv2d_add_nn_relu_1_p0_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_conv2d_add_nn_relu_1_p1_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_conv2d_add_nn_relu_1_p2_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_conv2d_add_nn_relu_1_T_relu_strides == NULL))
    {
    }
    for (int32_t ax0_ax1_outer_fused = 0; ax0_ax1_outer_fused < 42; ++ax0_ax1_outer_fused)
    {
        float PadInput[32];
        float conv[16];
        for (int32_t i1 = 0; i1 < 4; ++i1)
        {
            for (int32_t i3 = 0; i3 < 8; ++i3)
            {
                int32_t cse_var_2 = (i1 + ax0_ax1_outer_fused);
                int32_t cse_var_1 = (i1 * 8);
                PadInput[(cse_var_1 + i3)] =
                    (((1 <= cse_var_2) && (cse_var_2 < 43))
                         ? ((float *)p0_1)[(((cse_var_1 + (ax0_ax1_outer_fused * 8)) + i3) - 8)]
                         : 0.000000e+00f);
            }
        }
        for (int32_t oco = 0; oco < 2; ++oco)
        {
            for (int32_t oci_init = 0; oci_init < 8; ++oci_init)
            {
                conv[((oco * 8) + oci_init)] = 0.000000e+00f;
            }
            for (int32_t kh = 0; kh < 4; ++kh)
            {
                for (int32_t ic = 0; ic < 8; ++ic)
                {
                    for (int32_t oci = 0; oci < 8; ++oci)
                    {
                        int32_t cse_var_4 = (oco * 8);
                        int32_t cse_var_3 = (cse_var_4 + oci);
                        conv[cse_var_3] =
                            (conv[cse_var_3] + (PadInput[((kh * 8) + ic)] *
                                                ((float *)p1_1)[((((kh * 128) + (ic * 16)) + cse_var_4) + oci)]));
                    }
                }
            }
        }
        for (int32_t ax3_outer = 0; ax3_outer < 2; ++ax3_outer)
        {
            for (int32_t ax3_inner = 0; ax3_inner < 8; ++ax3_inner)
            {
                int32_t cse_var_6 = (ax3_outer * 8);
                int32_t cse_var_5 = (cse_var_6 + ax3_inner);
                float v_ = conv[cse_var_5] + ((float *)p2_1)[cse_var_5];
                ((float *)T_relu_1)[(((ax0_ax1_outer_fused * 16) + cse_var_6) + ax3_inner)] =
                    ((v_) > (0.000000e+00f) ? (v_) : (0.000000e+00f));
            }
        }
    }
    return 0;
}

#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_dense_add(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
                                      int32_t *out_ret_tcode, void *resource_handle)
{
    void *p0 = (((TVMValue *)args)[0].v_handle);
    void *p1 = (((TVMValue *)args)[1].v_handle);
    void *p2 = (((TVMValue *)args)[2].v_handle);
    void *T_add = (((TVMValue *)args)[3].v_handle);
    void *p0_1 = (((DLTensor *)p0)[0].data);
    void *tvmgen_default_fused_nn_dense_add_p0_strides = (((DLTensor *)p0)[0].strides);
    void *p1_1 = (((DLTensor *)p1)[0].data);
    void *tvmgen_default_fused_nn_dense_add_p1_strides = (((DLTensor *)p1)[0].strides);
    void *p2_1 = (((DLTensor *)p2)[0].data);
    void *tvmgen_default_fused_nn_dense_add_p2_strides = (((DLTensor *)p2)[0].strides);
    void *T_add_1 = (((DLTensor *)T_add)[0].data);
    void *tvmgen_default_fused_nn_dense_add_T_add_strides = (((DLTensor *)T_add)[0].strides);
    if (!(tvmgen_default_fused_nn_dense_add_p0_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_dense_add_p1_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_dense_add_p2_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_dense_add_T_add_strides == NULL))
    {
    }
    float packed_weight[64];
    float compute_global[4];
    for (int32_t y = 0; y < 16; ++y)
    {
        for (int32_t x = 0; x < 4; ++x)
        {
            packed_weight[((y * 4) + x)] = ((float *)p1_1)[((x * 16) + y)];
        }
    }
    for (int32_t x_c_init = 0; x_c_init < 4; ++x_c_init)
    {
        compute_global[x_c_init] = 0.000000e+00f;
    }
    for (int32_t k_outer = 0; k_outer < 16; ++k_outer)
    {
        for (int32_t x_c = 0; x_c < 4; ++x_c)
        {
            compute_global[x_c] =
                (compute_global[x_c] + (((float *)p0_1)[k_outer] * packed_weight[((k_outer * 4) + x_c)]));
        }
    }
    for (int32_t ax1_inner_inner = 0; ax1_inner_inner < 4; ++ax1_inner_inner)
    {
        ((float *)T_add_1)[ax1_inner_inner] = (compute_global[ax1_inner_inner] + ((float *)p2_1)[ax1_inner_inner]);
    }
    return 0;
}

#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_dense_add_nn_relu(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
                                              int32_t *out_ret_tcode, void *resource_handle)
{
    void *p0 = (((TVMValue *)args)[0].v_handle);
    void *p1 = (((TVMValue *)args)[1].v_handle);
    void *p2 = (((TVMValue *)args)[2].v_handle);
    void *T_relu = (((TVMValue *)args)[3].v_handle);
    void *p0_1 = (((DLTensor *)p0)[0].data);
    void *tvmgen_default_fused_nn_dense_add_nn_relu_p0_strides = (((DLTensor *)p0)[0].strides);
    void *p1_1 = (((DLTensor *)p1)[0].data);
    void *tvmgen_default_fused_nn_dense_add_nn_relu_p1_strides = (((DLTensor *)p1)[0].strides);
    void *p2_1 = (((DLTensor *)p2)[0].data);
    void *tvmgen_default_fused_nn_dense_add_nn_relu_p2_strides = (((DLTensor *)p2)[0].strides);
    void *T_relu_1 = (((DLTensor *)T_relu)[0].data);
    void *tvmgen_default_fused_nn_dense_add_nn_relu_T_relu_strides = (((DLTensor *)T_relu)[0].strides);
    if (!(tvmgen_default_fused_nn_dense_add_nn_relu_p0_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_dense_add_nn_relu_p1_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_dense_add_nn_relu_p2_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_dense_add_nn_relu_T_relu_strides == NULL))
    {
    }
    for (int32_t ax1_outer_ax0_outer_fused = 0; ax1_outer_ax0_outer_fused < 2; ++ax1_outer_ax0_outer_fused)
    {
        float compute_global[8];
        for (int32_t x_c_init = 0; x_c_init < 8; ++x_c_init)
        {
            compute_global[x_c_init] = 0.000000e+00f;
        }
        for (int32_t k_outer = 0; k_outer < 224; ++k_outer)
        {
            for (int32_t x_c = 0; x_c < 8; ++x_c)
            {
                compute_global[x_c] =
                    (compute_global[x_c] +
                     (((float *)p0_1)[k_outer] *
                      ((float *)p1_1)[(((ax1_outer_ax0_outer_fused * 1792) + (k_outer * 8)) + x_c)]));
            }
        }
        for (int32_t ax1_inner_inner = 0; ax1_inner_inner < 8; ++ax1_inner_inner)
        {
            int32_t cse_var_2 = ((ax1_outer_ax0_outer_fused * 8) + ax1_inner_inner);
            float v_ = compute_global[ax1_inner_inner] + ((float *)p2_1)[cse_var_2];
            ((float *)T_relu_1)[cse_var_2] = ((v_) > (0.000000e+00f) ? (v_) : (0.000000e+00f));
        }
    }
    return 0;
}

#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_max_pool2d(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
                                       int32_t *out_ret_tcode, void *resource_handle)
{
    void *p0 = (((TVMValue *)args)[0].v_handle);
    void *pool_max = (((TVMValue *)args)[1].v_handle);
    void *p0_1 = (((DLTensor *)p0)[0].data);
    void *tvmgen_default_fused_nn_max_pool2d_p0_strides = (((DLTensor *)p0)[0].strides);
    void *pool_max_1 = (((DLTensor *)pool_max)[0].data);
    void *tvmgen_default_fused_nn_max_pool2d_pool_max_strides = (((DLTensor *)pool_max)[0].strides);
    if (!(tvmgen_default_fused_nn_max_pool2d_p0_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_max_pool2d_pool_max_strides == NULL))
    {
    }
    for (int32_t ax1 = 0; ax1 < 42; ++ax1)
    {
        for (int32_t ax3 = 0; ax3 < 8; ++ax3)
        {
            ((float *)pool_max_1)[((ax1 * 8) + ax3)] = -3.402823e+38f;
            for (int32_t rv0 = 0; rv0 < 3; ++rv0)
            {
                for (int32_t rv1 = 0; rv1 < 3; ++rv1)
                {
                    int32_t cse_var_1 = ((ax1 * 8) + ax3);
                    float v_ = ((float *)pool_max_1)[cse_var_1];
                    float v__1 = ((float *)p0_1)[((((ax1 * 72) + (rv0 * 24)) + (rv1 * 8)) + ax3)];
                    ((float *)pool_max_1)[cse_var_1] = ((v_) > (v__1) ? (v_) : (v__1));
                }
            }
        }
    }
    return 0;
}

#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_max_pool2d_1(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
                                         int32_t *out_ret_tcode, void *resource_handle)
{
    void *p0 = (((TVMValue *)args)[0].v_handle);
    void *pool_max = (((TVMValue *)args)[1].v_handle);
    void *p0_1 = (((DLTensor *)p0)[0].data);
    void *tvmgen_default_fused_nn_max_pool2d_1_p0_strides = (((DLTensor *)p0)[0].strides);
    void *pool_max_1 = (((DLTensor *)pool_max)[0].data);
    void *tvmgen_default_fused_nn_max_pool2d_1_pool_max_strides = (((DLTensor *)pool_max)[0].strides);
    if (!(tvmgen_default_fused_nn_max_pool2d_1_p0_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_max_pool2d_1_pool_max_strides == NULL))
    {
    }
    for (int32_t ax1 = 0; ax1 < 14; ++ax1)
    {
        for (int32_t ax3 = 0; ax3 < 16; ++ax3)
        {
            ((float *)pool_max_1)[((ax1 * 16) + ax3)] = -3.402823e+38f;
            for (int32_t rv0 = 0; rv0 < 3; ++rv0)
            {
                int32_t cse_var_1 = ((ax1 * 16) + ax3);
                float v_ = ((float *)pool_max_1)[cse_var_1];
                float v__1 = ((float *)p0_1)[(((ax1 * 48) + (rv0 * 16)) + ax3)];
                ((float *)pool_max_1)[cse_var_1] = ((v_) > (v__1) ? (v_) : (v__1));
            }
        }
    }
    return 0;
}

#ifdef __cplusplus
extern "C"
#endif
    TVM_DLL int32_t
    tvmgen_default_fused_nn_softmax(void *args, int32_t *arg_type_ids, int32_t num_args, void *out_ret_value,
                                    int32_t *out_ret_tcode, void *resource_handle)
{
    void *p0 = (((TVMValue *)args)[0].v_handle);
    void *T_softmax_norm = (((TVMValue *)args)[1].v_handle);
    void *p0_1 = (((DLTensor *)p0)[0].data);
    void *tvmgen_default_fused_nn_softmax_p0_strides = (((DLTensor *)p0)[0].strides);
    void *T_softmax_norm_1 = (((DLTensor *)T_softmax_norm)[0].data);
    void *tvmgen_default_fused_nn_softmax_T_softmax_norm_strides = (((DLTensor *)T_softmax_norm)[0].strides);
    if (!(tvmgen_default_fused_nn_softmax_p0_strides == NULL))
    {
    }
    if (!(tvmgen_default_fused_nn_softmax_T_softmax_norm_strides == NULL))
    {
    }
    float T_softmax_maxelem[1];
    float T_softmax_exp[4];
    float T_softmax_expsum[1];
    T_softmax_maxelem[0] = -3.402823e+38f;
    for (int32_t k = 0; k < 4; ++k)
    {
        float v_ = T_softmax_maxelem[0];
        float v__1 = ((float *)p0_1)[k];
        T_softmax_maxelem[0] = ((v_) > (v__1) ? (v_) : (v__1));
    }
    for (int32_t i1 = 0; i1 < 4; ++i1)
    {
        T_softmax_exp[i1] = expf((((float *)p0_1)[i1] - T_softmax_maxelem[0]));
    }
    T_softmax_expsum[0] = 0.000000e+00f;
    for (int32_t k_1 = 0; k_1 < 4; ++k_1)
    {
        T_softmax_expsum[0] = (T_softmax_expsum[0] + T_softmax_exp[k_1]);
    }
    for (int32_t i1_1 = 0; i1_1 < 4; ++i1_1)
    {
        ((float *)T_softmax_norm_1)[i1_1] = (T_softmax_exp[i1_1] / T_softmax_expsum[0]);
    }
    return 0;
}
