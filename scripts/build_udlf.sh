#!/usr/bin/env bash
# Build the official UDLF binary from source, pinned to a release tag.
#
# Usage:
#   scripts/build_udlf.sh [DEST_DIR] [TAG]
#
# Defaults: DEST_DIR=.udlf (inside the repository, ignored by git), TAG=v1.70
# The binary ends up at DEST_DIR/UDLF/bin/udlf, next to the reference config.ini.
# The test suite finds it there automatically (or via the UDLF_BIN env var).
set -euo pipefail

DEST_DIR="${1:-.udlf}"
TAG="${2:-v1.70}"
REPO_URL="https://github.com/UDLF/UDLF.git"

mkdir -p "$DEST_DIR"
cd "$DEST_DIR"

if [ ! -d UDLF/.git ]; then
    git -c advice.detachedHead=false clone --quiet --depth 1 --branch "$TAG" "$REPO_URL" UDLF
else
    git -C UDLF fetch --quiet --depth 1 origin tag "$TAG"
    git -C UDLF -c advice.detachedHead=false checkout --quiet "$TAG"
fi

make -C UDLF -j"$(nproc 2>/dev/null || echo 2)" >/dev/null
echo "UDLF $TAG built at $(pwd)/UDLF/bin/udlf"
