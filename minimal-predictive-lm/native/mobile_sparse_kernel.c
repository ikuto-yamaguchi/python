#include <stdint.h>
#include <stddef.h>
#include <string.h>


typedef struct {
    int embedding_dim;
    int block_dim;
    int rank;
    int active_blocks;
} mpm_mobile_shape;


static int16_t clamp_i16(int32_t value) {
    if (value > 32767) return 32767;
    if (value < -32768) return -32768;
    return (int16_t)value;
}


/*
 * Generic C99 int8 kernel suitable for Android NDK builds. The caller supplies
 * only the already-routed active blocks, so token-step runtime is independent
 * of total model capacity. No allocation occurs inside this function.
 */
void mpm_mobile_sparse_step(
    const mpm_mobile_shape *shape,
    const int8_t *embedding,
    const int8_t *input_weights,
    const int8_t *left_weights,
    const int8_t *right_weights,
    const int8_t *decoder_weights,
    int16_t *states,
    int32_t *logits,
    int32_t activation_shift,
    int32_t decoder_shift
) {
    const int e = shape->embedding_dim;
    const int d = shape->block_dim;
    const int r = shape->rank;
    const int a = shape->active_blocks;
    memset(logits, 0, 256 * sizeof(*logits));

    for (int block = 0; block < a; ++block) {
        const int8_t *in = input_weights + (size_t)block * e * d;
        const int8_t *left = left_weights + (size_t)block * d * r;
        const int8_t *right = right_weights + (size_t)block * r * d;
        const int8_t *decoder = decoder_weights + (size_t)block * d * 256;
        int16_t *state = states + (size_t)block * d;
        int32_t hidden[64];

        if (r > 64) return;

        for (int j = 0; j < r; ++j) {
            int32_t sum = 0;
            for (int i = 0; i < d; ++i) {
                sum += (int32_t)state[i] * (int32_t)left[(size_t)i * r + j];
            }
            hidden[j] = sum >> activation_shift;
        }

        for (int j = 0; j < d; ++j) {
            int32_t proposal = 0;
            for (int i = 0; i < e; ++i) {
                proposal += (int32_t)embedding[i]
                    * (int32_t)in[(size_t)i * d + j];
            }
            for (int i = 0; i < r; ++i) {
                proposal += hidden[i]
                    * (int32_t)right[(size_t)i * d + j];
            }
            proposal >>= activation_shift;
            state[j] = clamp_i16(((int32_t)state[j] * 7 + proposal) >> 3);
        }

        for (int token = 0; token < 256; ++token) {
            int32_t sum = 0;
            for (int i = 0; i < d; ++i) {
                sum += (int32_t)state[i]
                    * (int32_t)decoder[(size_t)i * 256 + token];
            }
            logits[token] += sum >> decoder_shift;
        }
    }
}


#ifdef MPM_MOBILE_KERNEL_TEST_MAIN
#include <stdio.h>

int main(void) {
    const mpm_mobile_shape shape = {8, 16, 4, 2};
    int8_t embedding[8];
    int8_t input[2 * 8 * 16];
    int8_t left[2 * 16 * 4];
    int8_t right[2 * 4 * 16];
    int8_t decoder[2 * 16 * 256];
    int16_t states[2 * 16] = {0};
    int32_t logits[256];
    for (size_t i = 0; i < sizeof(embedding); ++i)
        embedding[i] = (int8_t)((i % 5) - 2);
    for (size_t i = 0; i < sizeof(input); ++i)
        input[i] = (int8_t)((i % 7) - 3);
    for (size_t i = 0; i < sizeof(left); ++i)
        left[i] = (int8_t)((i % 3) - 1);
    for (size_t i = 0; i < sizeof(right); ++i)
        right[i] = (int8_t)((i % 5) - 2);
    for (size_t i = 0; i < sizeof(decoder); ++i)
        decoder[i] = (int8_t)((i % 11) - 5);
    mpm_mobile_sparse_step(
        &shape, embedding, input, left, right, decoder,
        states, logits, 4, 4
    );
    long long checksum = 0;
    for (int i = 0; i < 256; ++i) checksum += logits[i];
    printf("checksum=%lld state0=%d\n", checksum, states[0]);
    return checksum == 0 && states[0] == 0;
}
#endif
