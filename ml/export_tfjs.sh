#!/usr/bin/env bash
# ISL Model Export Script: Keras -> TensorFlow.js Web Model
# Ensures the model is quantized and optimized for client-side Web Worker execution.

set -e

INPUT_MODEL="${1:-isl_model.keras}"
OUTPUT_DIR="${2:-../web/public/models/tfjs_model}"

echo "=================================================="
echo "Exporting ISL Model to TensorFlow.js"
echo "Input : ${INPUT_MODEL}"
echo "Output: ${OUTPUT_DIR}"
echo "=================================================="

if [ ! -f "${INPUT_MODEL}" ]; then
    echo "Warning: Model checkpoint ${INPUT_MODEL} does not exist yet."
    echo "Run 'python ml/train.py' first."
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"

# Convert using float16 quantization for compact download (<15MB)
tensorflowjs_converter \
    --input_format=keras \
    --quantize_float16 \
    "${INPUT_MODEL}" \
    "${OUTPUT_DIR}"

echo "Export completed successfully. Model files generated in ${OUTPUT_DIR}"
