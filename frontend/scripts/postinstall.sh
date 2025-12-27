#!/bin/bash
# Copy ONNX Runtime WASM files from node_modules to public directory
# Required for @ricky0123/vad-react to load ONNX models in the browser

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(dirname "$SCRIPT_DIR")"
NODE_MODULES_ONNX="$FRONTEND_DIR/node_modules/onnxruntime-web/dist"
PUBLIC_DIR="$FRONTEND_DIR/public"

# Files required for VAD ONNX runtime
FILES=(
    "ort-wasm-simd-threaded.wasm"
    "ort-wasm-simd-threaded.mjs"
    "ort-wasm-simd-threaded.asyncify.wasm"
)

echo "Copying ONNX Runtime WASM files to public directory..."

for file in "${FILES[@]}"; do
    if [ -f "$NODE_MODULES_ONNX/$file" ]; then
        cp "$NODE_MODULES_ONNX/$file" "$PUBLIC_DIR/"
        echo "  ✓ Copied $file"
    else
        echo "  ⚠ Warning: $file not found in node_modules"
    fi
done

echo "Done."
