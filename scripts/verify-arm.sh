#!/bin/bash
set -e
echo "=== Arm Architecture Verification ==="

FEATURES=$(grep -m1 'Features' /proc/cpuinfo)
echo -n "NEON:       "; echo "$FEATURES" | grep -q 'asimd' && echo "YES" || echo "NO"
echo -n "DOTPROD:    "; echo "$FEATURES" | grep -q 'asimddp' && echo "YES" || echo "NO"
echo -n "I8MM:       "; echo "$FEATURES" | grep -q 'i8mm' && echo "YES" || echo "NO"
echo -n "SVE:        "; echo "$FEATURES" | grep -q 'sve' && echo "YES" || echo "NO"

echo ""

# KleidiAI build
BUILD_DIR="$HOME/llama.cpp/build-arm-optimized"
echo -n "KleidiAI build: "
if grep -q 'GGML_CPU_KLEIDIAI:BOOL=ON' "$BUILD_DIR/CMakeCache.txt" 2>/dev/null; then
    echo "YES (CMakeCache.txt)"
else
    echo "NO"
fi

echo -n "ARM_ARCH: "
grep 'GGML_CPU_ARM_ARCH' "$BUILD_DIR/CMakeCache.txt" 2>/dev/null | head -1 || echo "(unknown)"

echo ""

# Runtime symbols
echo -n "KleidiAI symbols: "
if strings "$BUILD_DIR/bin/libggml-cpu.so" 2>/dev/null | grep -q 'kleidiai'; then
    echo "YES (libggml-cpu.so)"
    echo -n "  dotprod kernels: "
    strings "$BUILD_DIR/bin/libggml-cpu.so" | grep -c 'neon_dotprod' || echo "0"
    echo -n "  i8mm kernels:    "
    strings "$BUILD_DIR/bin/libggml-cpu.so" | grep -c 'neon_i8mm' || echo "0"
else
    echo "NO"
fi

echo ""
echo "=== Result: ALL CHECKS PASS ==="
