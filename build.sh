#!/bin/bash
set -euo pipefail

cd /build

make NO_SUDO=1 \
     USE_LUA="${USE_LUA:-0}" \
     USE_PROMETHEUS="${USE_PROMETHEUS:-0}" \
     RELEASE="${RELEASE:-1}"

# Hand the built packages back to the host through the /RPMS bind mount
if [ -d /RPMS ]; then
    find ./rpmbuild/RPMS ./rpmbuild/SRPMS -name '*.rpm' -exec cp -v {} /RPMS/ \;
fi
