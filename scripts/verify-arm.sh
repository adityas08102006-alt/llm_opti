#!/bin/bash
# shellcheck disable=SC2312
echo "=== Arm Architecture Verification ==="

FEATURES=$(grep -m1 'Features' /proc/cpuinfo)
HAVE_NEON=false; HAVE_DOTPROD=false; HAVE_I8MM=false; HAVE_SVE=false
echo "$FEATURES" | grep -q 'asimd'   && HAVE_NEON=true   && echo "NEON:       YES" || echo "NEON:       NO"
echo "$FEATURES" | grep -q 'asimddp' && HAVE_DOTPROD=true && echo "DOTPROD:    YES" || echo "DOTPROD:    NO"
echo "$FEATURES" | grep -q 'i8mm'    && HAVE_I8MM=true    && echo "I8MM:       YES" || echo "I8MM:       NO"
echo "$FEATURES" | grep -q 'sve'     && HAVE_SVE=true     && echo "SVE:        YES" || echo "SVE:        NO"

echo ""

# KleidiAI build
BUILD_DIR="$HOME/llama.cpp/build-arm-optimized"
HAVE_KLEIDIAI=false
if grep -q 'GGML_CPU_KLEIDIAI:BOOL=ON' "$BUILD_DIR/CMakeCache.txt" 2>/dev/null; then
    HAVE_KLEIDIAI=true
    echo "KleidiAI build: YES (CMakeCache.txt)"
else
    echo "KleidiAI build: NO"
fi

ARM_ARCH=$(grep 'GGML_CPU_ARM_ARCH' "$BUILD_DIR/CMakeCache.txt" 2>/dev/null | head -1 || echo "GGML_CPU_ARM_ARCH:STRING=(unknown)")
echo "ARM_ARCH: $ARM_ARCH"

echo ""

# Runtime symbols
HAVE_SYMBOLS=false
if strings "$BUILD_DIR/bin/libggml-cpu.so" 2>/dev/null | grep -q 'kleidiai'; then
    HAVE_SYMBOLS=true
    echo "KleidiAI symbols: YES (libggml-cpu.so)"
    echo -n "  dotprod kernels: "
    strings "$BUILD_DIR/bin/libggml-cpu.so" | grep -c 'neon_dotprod' || echo "0"
    echo -n "  i8mm kernels:    "
    strings "$BUILD_DIR/bin/libggml-cpu.so" | grep -c 'neon_i8mm' || echo "0"
else
    echo "KleidiAI symbols: NO"
fi

echo ""

# Computed result
FAILURES=""
$HAVE_NEON     || FAILURES="${FAILURES}NEON "
$HAVE_DOTPROD  || FAILURES="${FAILURES}DOTPROD "
$HAVE_I8MM     || FAILURES="${FAILURES}I8MM "
$HAVE_KLEIDIAI || FAILURES="${FAILURES}KLEIDIAI_BUILD "
$HAVE_SYMBOLS  || FAILURES="${FAILURES}KLEIDIAI_SYMBOLS "

if [ -z "$FAILURES" ]; then
    echo "=== Result: ALL CHECKS PASS ==="
else
    echo "=== Result: FAILED — ${FAILURES}==="
    exit 1
fi
