#!/bin/bash
#
# 설정 예제 하나를 문법 검사합니다.
#
# 예제 파일에는 frontend/backend/listen 블록만 들어 있어 그대로는 검사할 수
# 없습니다. 이 스크립트가 같은 디렉터리의 00-base.cfg(global/defaults 뼈대)를
# 앞에 붙여서 haproxy -c 를 돌려 줍니다.
#
# 사용법:
#   check-example.sh 01-web-http-lb.cfg    예제 하나 검사
#   check-example.sh --all                 모든 예제 검사
#
set -u

EXAMPLE_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
BASE="${EXAMPLE_DIR}/00-base.cfg"
HAPROXY="${HAPROXY:-/usr/sbin/haproxy}"

usage() {
    cat <<EOF
사용법: $(basename "$0") <예제파일> | --all

  <예제파일>   예제 파일 이름 또는 경로. 이름만 적으면
               ${EXAMPLE_DIR} 안에서 찾습니다.
  --all        00-base.cfg 를 뺀 모든 예제를 차례로 검사합니다.

검사할 수 있는 예제:
EOF
    for f in "${EXAMPLE_DIR}"/*.cfg; do
        [ "$f" = "$BASE" ] && continue
        echo "  $(basename "$f")"
    done
}

check_one() {
    local target="$1"

    if [ ! -f "$target" ]; then
        target="${EXAMPLE_DIR}/${1}"
    fi
    if [ ! -f "$target" ]; then
        echo "오류: 예제 파일을 찾을 수 없습니다: $1" >&2
        return 2
    fi

    echo "== $(basename "$target")"

    # HAProxy 3.x는 문제가 없으면 아무 말도 하지 않습니다. 그대로 두면 통과인지
    # 아직 안 돌았는지 구분이 안 되므로, 출력을 받아 두었다가 결과를 직접 알려
    # 줍니다. 경고는 종료 코드 0이라 따로 찾아내야 합니다.
    local out rc
    out="$("$HAPROXY" -c -f "$BASE" -f "$target" 2>&1)"
    rc=$?

    [ -n "$out" ] && echo "$out"

    if [ "$rc" -eq 0 ]; then
        case "$out" in
            *"Warnings were found"*)
                echo "   통과 — 다만 위 경고는 확인해 보세요."
                ;;
            *)
                echo "   통과 — 문법 이상 없음."
                ;;
        esac
        return 0
    fi

    echo "   검사 실패. 위 메시지를 확인하세요." >&2
    case "$(basename "$target")" in
        03-*|04-*)
            echo "   이 예제는 /etc/haproxy/certs/example.com.pem 인증서 파일이" >&2
            echo "   실제로 있어야 통과합니다. 만드는 방법은 예제 파일 주석 참고." >&2
            ;;
    esac
    return 1
}

if [ $# -ne 1 ]; then
    usage >&2
    exit 2
fi

case "$1" in
    -h|--help)
        usage
        exit 0
        ;;
esac

if [ ! -x "$HAPROXY" ]; then
    echo "오류: haproxy 실행 파일이 없습니다: $HAPROXY" >&2
    echo "      다른 경로에 있다면 HAPROXY=/경로/haproxy $(basename "$0") ... 로 지정하세요." >&2
    exit 2
fi

if [ ! -f "$BASE" ]; then
    echo "오류: 뼈대 파일이 없습니다: $BASE" >&2
    exit 2
fi

if [ "$1" = "--all" ]; then
    rc=0
    for f in "${EXAMPLE_DIR}"/*.cfg; do
        [ "$f" = "$BASE" ] && continue
        check_one "$f" || rc=1
        echo
    done
    if [ "$rc" -eq 0 ]; then
        echo "모든 예제가 문법 검사를 통과했습니다."
    else
        echo "일부 예제가 검사를 통과하지 못했습니다." >&2
    fi
    exit "$rc"
fi

check_one "$1"
