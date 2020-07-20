#!/bin/bash
# Common bash functions useful for cross-compiling Certbot snaps.

# Resolve the Snap architecture to Docker architecture (DOCKER_ARCH variable)
# and QEMU architecture (QEMU_ARCH variable).
# Usage: ResolveArch [amd64|arm64|armhf]
ResolveArch() {
    local SNAP_ARCH=$1

    case "${SNAP_ARCH}" in
        "amd64")
            DOCKER_ARCH="amd64"
            QEMU_ARCH="x86_64"
            ;;
        "arm64")
            DOCKER_ARCH="arm64v8"
            QEMU_ARCH="aarch64"
            ;;
        "armhf")
            DOCKER_ARCH="arm32v7"
            QEMU_ARCH="arm"
            ;;
        "*")
            echo "Not supported build architecture '$1'." >&2
            exit 1
    esac
}

# Super temporary and hacky method to get a very precise version of the snapcraft docker
# image to avoid failures on QEMU arm64 with recent versions of the docker image.
# Usage: GetSnapcraftDockerImage [amd64|arm64|armhf]
GetSnapcraftDockerImage() {
  local SNAP_ARCH=$1

  case "${SNAP_ARCH}" in
    "amd64")
      echo "adferrand/snapcraft@sha256:fbd1f45e88cf249c5cefff1a20b599c34f4d9b7baad2177826cf29484bc944d6"
      ;;
    "arm64")
      echo "adferrand/snapcraft@sha256:b4e2749040917931a6da0b3596df8ecb07b9e241d1cfea69b18a58b9721d1e75"
      ;;
    "armhf")
      echo "adferrand/snapcraft@sha256:0c2a43d5aa8911d9d2ccbc8622c161f821b721d099c299f7b882e534869f2f50"
      ;;
    "*")
      echo "Not supported build architecture '$1'." >&2
      exit 1
  esac
}

# Downloads QEMU static binary file for architecture
# Usage: DownloadQemuStatic [x86_64|aarch64|arm] DEST_DIR
DownloadQemuStatic() {
    local QEMU_ARCH=$1
    local DEST_DIR=$2
    local QEMU_DOWNLOAD_URL
    local QEMU_LATEST_TAG

    if [ ! -f "${DIR}/qemu-${QEMU_ARCH}-static" ]; then
        QEMU_DOWNLOAD_URL="https://github.com/multiarch/qemu-user-static/releases/download"
        QEMU_LATEST_TAG=$(curl -s https://api.github.com/repos/multiarch/qemu-user-static/tags \
            | grep 'name.*v[0-9]' \
            | head -n 1 \
            | cut -d '"' -f 4)
        echo "${QEMU_DOWNLOAD_URL}/${QEMU_LATEST_TAG}/x86_64_qemu-${QEMU_ARCH}-static.tar.gz"
        curl -SL "${QEMU_DOWNLOAD_URL}/${QEMU_LATEST_TAG}/x86_64_qemu-${QEMU_ARCH}-static.tar.gz" \
            | tar xzv -C "${DEST_DIR}"
    fi
}

# Executes the QEMU register script
# Usage: RegisterQemuHandlers
RegisterQemuHandlers() {
    docker run --rm --privileged multiarch/qemu-user-static:register --reset
}
