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
# Needs g++ with C++23 and OpenMP, TBB (libtbb-dev) and jemalloc. Without the
# jemalloc development package (libjemalloc-dev) the binaries are linked
# against the runtime library (libjemalloc.so.2) directly.
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

MAKE_ARGS=()
if ! echo 'int main(){}' | g++ -x c++ - -o /dev/null -ljemalloc 2>/dev/null; then
    JEMALLOC=$(ldconfig -p 2>/dev/null | grep -o '/[^ ]*libjemalloc\.so\.2$' | head -n 1 || true)
    if [ -z "$JEMALLOC" ]; then
        echo "jemalloc not found: install it (Debian/Ubuntu: sudo apt install libjemalloc-dev)" >&2
        exit 1
    fi
    MAKE_ARGS+=("LDFLAGS=-lm -lpthread -ltbb -l:$(basename "$JEMALLOC") -lgomp")
fi

make -j"$(nproc 2>/dev/null || echo 2)" udlf udlf-strict "${MAKE_ARGS[@]}" >/dev/null
echo "Sparse UDLF $COMMIT built at $(pwd)/bin (udlf, udlf_strict)"
