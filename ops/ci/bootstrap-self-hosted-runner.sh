#!/usr/bin/env bash
set -euo pipefail

EXPECTED_HOST="kgm-e4-owner-pilot"
EXPECTED_ARCH="aarch64"
REPO_URL="https://github.com/kolemasakar/K_Supervisor"
RUNNER_VERSION="2.337.0"
RUNNER_ARCHIVE="actions-runner-linux-arm64-${RUNNER_VERSION}.tar.gz"
RUNNER_SHA256="9b1dc70626422526e3c94767cf024896beb15da5342a3f4819bf2feac13e0393"
SOURCE_ARCHIVE="/home/kgmops/runner-bootstrap/${RUNNER_ARCHIVE}"

RUNNER_USER="ghrunner"
RUNNER_HOME="/home/${RUNNER_USER}"
RUNNER_DIR="/opt/actions-runner/k-supervisor"
RUNNER_NAME="kgm-e4-owner-pilot"
RUNNER_LABELS="k-supervisor-ci"

SWAPFILE="/swapfile"
SWAP_SIZE="2G"
LTTNG_PACKAGE="liblttng-ust1t64"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

[[ "$(id -u)" -eq 0 ]] || fail "root is required through the approved owner path"
[[ "$(hostname)" == "${EXPECTED_HOST}" ]] || fail "wrong host: $(hostname)"
[[ "$(uname -m)" == "${EXPECTED_ARCH}" ]] || fail "wrong architecture: $(uname -m)"
[[ -f "${SOURCE_ARCHIVE}" ]] || fail "runner archive missing: ${SOURCE_ARCHIVE}"

echo "${RUNNER_SHA256}  ${SOURCE_ARCHIVE}" | sha256sum -c -

if ! id "${RUNNER_USER}" >/dev/null 2>&1; then
  useradd --system --create-home --home-dir "${RUNNER_HOME}"     --shell /usr/sbin/nologin --user-group "${RUNNER_USER}"
fi
passwd -l "${RUNNER_USER}" >/dev/null 2>&1 || true

for group in sudo adm docker lxd; do
  gpasswd -d "${RUNNER_USER}" "${group}" >/dev/null 2>&1 || true
done

if id -nG "${RUNNER_USER}" | tr " " "\n" | grep -Eq "^(sudo|adm|docker|lxd)$"; then
  fail "${RUNNER_USER} still has privileged group membership"
fi
if runuser -u "${RUNNER_USER}" -- test -r /home/kgmops 2>/dev/null; then
  fail "${RUNNER_USER} can read /home/kgmops"
fi
if runuser -u "${RUNNER_USER}" -- test -x /home/kgmops 2>/dev/null; then
  fail "${RUNNER_USER} can traverse /home/kgmops"
fi

if [[ -e "${RUNNER_DIR}" ]] &&
   [[ -n "$(find "${RUNNER_DIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  fail "${RUNNER_DIR} already exists and is non-empty"
fi
install -d -m 0750 -o "${RUNNER_USER}" -g "${RUNNER_USER}" "${RUNNER_DIR}"
tar -xzf "${SOURCE_ARCHIVE}" -C "${RUNNER_DIR}"
chown -R "${RUNNER_USER}:${RUNNER_USER}" "${RUNNER_DIR}"

if ! dpkg-query -W -f='${Status}' "${LTTNG_PACKAGE}" 2>/dev/null | grep -q "ok installed"; then
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${LTTNG_PACKAGE}"
fi

missing=""
while IFS= read -r native; do
  if file "${native}" | grep -q "ELF"; then
    unresolved="$(ldd "${native}" 2>&1 | grep "not found" || true)"
    if [[ -n "${unresolved}" ]]; then
      missing+="${native}: ${unresolved}"$'\n'
    fi
  fi
done < <(find "${RUNNER_DIR}/bin" "${RUNNER_DIR}/externals" -maxdepth 3 -type f 2>/dev/null)
[[ -z "${missing}" ]] || fail "missing shared libraries: ${missing}"

if [[ -z "$(swapon --show=NAME --noheadings)" ]]; then
  [[ ! -e "${SWAPFILE}" ]] || fail "${SWAPFILE} already exists; review manually"
  fallocate -l "${SWAP_SIZE}" "${SWAPFILE}"
  chmod 0600 "${SWAPFILE}"
  mkswap "${SWAPFILE}" >/dev/null
  swapon "${SWAPFILE}"
  if ! grep -Eq "^/swapfile[[:space:]]+none[[:space:]]+swap" /etc/fstab; then
    printf '%s\n' "${SWAPFILE} none swap sw 0 0" >> /etc/fstab
  fi
fi

echo "Official interactive runner registration follows."
echo "Enter the short-lived repository registration token only at the GitHub runner prompt."

runuser -u "${RUNNER_USER}" -- env -i \
  HOME="${RUNNER_HOME}" \
  USER="${RUNNER_USER}" \
  LOGNAME="${RUNNER_USER}" \
  PATH="/usr/local/bin:/usr/bin:/bin" \
  LANG="C.UTF-8" \
  /bin/bash -c "
    set -euo pipefail
    umask 077
    cd '${RUNNER_DIR}'
    ./config.sh \
      --url '${REPO_URL}' \
      --name '${RUNNER_NAME}' \
      --labels '${RUNNER_LABELS}' \
      --work '_work'
  "

[[ -f "${RUNNER_DIR}/.runner" ]] || fail "registration did not produce .runner"
chmod 0600 "${RUNNER_DIR}"/.credentials* 2>/dev/null || true

cd "${RUNNER_DIR}"
./svc.sh install "${RUNNER_USER}"
[[ -f .service ]] || fail "service installation did not produce .service"

SERVICE_NAME="$(tr -d '\r\n' < .service)"
[[ "${SERVICE_NAME}" == actions.runner.*.service ]] || fail "unexpected service name"

DROPIN_DIR="/etc/systemd/system/${SERVICE_NAME}.d"
install -d -m 0755 "${DROPIN_DIR}"
cat > "${DROPIN_DIR}/10-k-supervisor-guardrails.conf" <<'EOF'
[Service]
CPUQuota=70%
MemoryHigh=1G
MemoryMax=1536M
TasksMax=128
NoNewPrivileges=true
PrivateTmp=true
ProtectProc=invisible
InaccessiblePaths=/home/kgmops
UMask=0077
EOF
chmod 0644 "${DROPIN_DIR}/10-k-supervisor-guardrails.conf"

systemctl daemon-reload
./svc.sh start
systemctl is-active --quiet "${SERVICE_NAME}" || fail "runner service is not active"

[[ "$(systemctl show "${SERVICE_NAME}" -p CPUQuotaPerSecUSec --value)" == "700ms" ]] || fail "CPUQuota guardrail mismatch"
[[ "$(systemctl show "${SERVICE_NAME}" -p MemoryHigh --value)" == "1073741824" ]] || fail "MemoryHigh guardrail mismatch"
[[ "$(systemctl show "${SERVICE_NAME}" -p MemoryMax --value)" == "1610612736" ]] || fail "MemoryMax guardrail mismatch"
[[ "$(systemctl show "${SERVICE_NAME}" -p TasksMax --value)" == "128" ]] || fail "TasksMax guardrail mismatch"
[[ "$(systemctl show "${SERVICE_NAME}" -p Restart --value)" == "no" ]] || fail "unexpected Restart policy override"

echo "SYSTEMD_MEMORY_GUARDRAIL=PASS"
echo "SYSTEMD_CPU_GUARDRAIL=PASS"
echo "SYSTEMD_TASKS_GUARDRAIL=PASS"
echo "RUNNER_BOOTSTRAP=PASS"
echo "SERVICE=${SERVICE_NAME}"
id "${RUNNER_USER}"
swapon --show
systemctl show "${SERVICE_NAME}"   -p User -p Group -p Restart -p CPUQuotaPerSecUSec -p MemoryHigh -p MemoryMax -p TasksMax   -p NoNewPrivileges -p PrivateTmp -p ProtectProc -p InaccessiblePaths   --no-pager

echo "Do not change the workflow until GitHub confirms this runner online and idle."
