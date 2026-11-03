#!/usr/bin/env bash
# Build Sparse UDLF (https://github.com/andreTomi/Sparse_UDLF), pinned to a commit.
#
# Usage:
#   scripts/build_sparse.sh [DEST_DIR] [COMMIT]
#
# Defaults: DEST_DIR=.udlf, COMMIT=de3c14c (the repository has no tags yet).
# Two binaries end up in DEST_DIR/Sparse_UDLF/bin:
#   udlf         built with -ffast-math: CPRR_SPARSE and LHRR_SPARSE;
#   udlf_strict  built without fast-math: every method (RDPAC, RFE and BFSTree
#                refuse to run in the fast-math binary).
# pyUDLF picks the right one for each method.
#
# Needs a C++ compiler with OpenMP (g++; CXX selects another one), TBB and
# jemalloc. Without the jemalloc development package (libjemalloc-dev) the
# binaries are linked against the runtime library (libjemalloc.so.2) directly.
# In an active conda environment (e.g. Miniforge, no root needed:
#   conda create -n udlf -c conda-forge python=3.12 gxx_linux-64 tbb-devel jemalloc make)
# its compiler ($CXX) and libraries are used. A compiler without C++23 (g++ < 11)
# builds with -std=gnu++17, which the sources support.
set -euo pipefail

DEST_DIR="${1:-.udlf}"
COMMIT="${2:-de3c14c}"
REPO_URL="https://github.com/andreTomi/Sparse_UDLF.git"

mkdir -p "$DEST_DIR"
cd "$DEST_DIR"

if [ ! -d Sparse_UDLF/.git ]; then
    git clone --quiet "$REPO_URL" Sparse_UDLF
fi
git -C Sparse_UDLF fetch --quiet origin
git -C Sparse_UDLF -c advice.detachedHead=false checkout --quiet --force "$COMMIT"
cd Sparse_UDLF

CXX="${CXX:-g++}"
LIB_FLAGS=""
if [ -n "${CONDA_PREFIX:-}" ]; then
    LIB_FLAGS="-L$CONDA_PREFIX/lib -Wl,-rpath,$CONDA_PREFIX/lib"
fi
links() {
    # shellcheck disable=SC2086
    echo 'int main(){}' | "$CXX" -x c++ - -o /dev/null $LIB_FLAGS "$@" 2>/dev/null
}

JEMALLOC="-ljemalloc"
if ! links -ljemalloc; then
    LIB=$( (ls "${CONDA_PREFIX:-/nonexistent}"/lib/libjemalloc.so.2 2>/dev/null;
            ldconfig -p 2>/dev/null | grep -o '/[^ ]*libjemalloc\.so\.2$') | head -n 1 || true)
    if [ -z "$LIB" ]; then
        echo "jemalloc not found: install it (Debian/Ubuntu: sudo apt install libjemalloc-dev;" \
             "without root: conda install -c conda-forge jemalloc)" >&2
        exit 1
    fi
    JEMALLOC="-l:$(basename "$LIB")"
fi
MAKE_ARGS=("CC=$CXX" "LDFLAGS=$LIB_FLAGS -lm -lpthread -ltbb $JEMALLOC -lgomp")
if ! echo 'int main(){}' | "$CXX" -std=gnu++23 -x c++ -fsyntax-only - 2>/dev/null; then
    echo "note: $CXX does not support C++23; building with -std=gnu++17" >&2
    MAKE_ARGS+=("BASE_FLAGS=-std=gnu++17 -O3 -g -fno-omit-frame-pointer -D_GNU_SOURCE")
fi

make -j"$(nproc 2>/dev/null || echo 2)" udlf udlf-strict "${MAKE_ARGS[@]}" >/dev/null
echo "Sparse UDLF $COMMIT built at $(pwd)/bin (udlf, udlf_strict)"
