# HAProxy 3 RPM 빌더

이 저장소는 **HAProxy 3.4.3**을 RHEL 계열 리눅스(Rocky Linux, AlmaLinux, CentOS, RHEL)에 바로 설치할 수 있는 **RPM 패키지로 만들어 주는 도구**입니다.

리눅스 배포판이 기본으로 제공하는 HAProxy는 안정성을 위해 보통 몇 년 전 버전에 머물러 있습니다. 예를 들어 Rocky Linux 9의 기본 저장소(AppStream)에는 HAProxy 2.8이 들어 있는데, 이 버전에는 ACME 자동 인증서 발급 같은 3.x 신규 기능이 없습니다. 최신 기능이 필요하다면 직접 소스를 받아 컴파일해야 하지만, 그렇게 설치하면 나중에 삭제나 업그레이드가 지저분해집니다.

이 저장소는 그 중간을 메웁니다. 최신 HAProxy 소스를 받아서 컴파일하되, 결과물을 **RPM 패키지로 포장**해 줍니다. 그래서 `dnf install`로 설치하고 `dnf remove`로 깔끔하게 지울 수 있으며, systemd 서비스 등록·로그 설정·로그 로테이션까지 모두 자동으로 잡힙니다.

> **처음 오셨다면** — [빠른 시작](#빠른-시작) 세 줄만 따라 하시면 됩니다. 나머지는 필요할 때 찾아보세요.

---

## 목차

- [빠른 시작](#빠른-시작)
- [무엇이 만들어지나요](#무엇이-만들어지나요)
- [빌드 준비하기](#빌드-준비하기)
- [방법 1 — Docker로 빌드하기 (권장)](#방법-1--docker로-빌드하기-권장)
- [방법 2 — 서버에서 직접 빌드하기](#방법-2--서버에서-직접-빌드하기)
- [빌드 옵션](#빌드-옵션)
- [설치하고 실행하기](#설치하고-실행하기)
- [통계(Stats) 페이지](#통계stats-페이지)
- [설정 파일 이해하기](#설정-파일-이해하기)
- [설정 예제 모음](#설정-예제-모음) — 웹 · HTTPS · 라우팅 · DB · TCP · 속도 제한
- [로그 확인하기](#로그-확인하기)
- [새 HAProxy 버전으로 올리기](#새-haproxy-버전으로-올리기)
- [문제가 생겼을 때](#문제가-생겼을-때)
- [참고 자료](#참고-자료)

---

## 빠른 시작

Docker만 설치되어 있으면 아래 세 줄로 끝납니다. 서버에 컴파일러를 깔 필요도 없습니다.

```bash
git clone https://github.com/DataDynamics/haproxy3-rpm-builder-internal.git
cd haproxy3-rpm-builder-internal
make run-docker
```

몇 분 뒤 `RPMS/` 디렉터리에 RPM 파일이 생깁니다. 이걸 대상 서버로 옮겨서 설치하면 됩니다.

```bash
sudo dnf install -y ./RPMS/haproxy-3.4.3-1.el9.x86_64.rpm
sudo systemctl enable --now haproxy
```

이제 브라우저에서 `http://<서버주소>:9000/haproxy_stats` 에 접속하면 통계 화면이 나옵니다. 자세한 내용은 [통계 페이지](#통계stats-페이지) 항목을 보세요.

---

## 무엇이 만들어지나요

빌드가 끝나면 RPM 파일 네 개가 생깁니다. 보통은 **첫 번째 것만 설치하면 됩니다.**

| 파일 | 크기 | 설명 |
|---|---|---|
| `haproxy-3.4.3-1.el9.x86_64.rpm` | 약 2.4 MB | **실제로 설치할 패키지.** HAProxy 본체와 설정 파일이 들어 있습니다. |
| `haproxy-3.4.3-1.el9.src.rpm` | 약 5.2 MB | 소스 RPM. 다른 곳에서 이 패키지를 그대로 재현해 빌드할 때 씁니다. |
| `haproxy-debuginfo-…rpm` | 약 48 KB | 디버깅 심볼. 장애 분석으로 코어 덤프를 뜯어볼 때만 필요합니다. |
| `haproxy-debugsource-…rpm` | 약 43 KB | 디버깅용 소스. 위와 같은 용도입니다. |

파일 이름의 `1`은 패키지 릴리스 번호이고 `el9`는 RHEL 9 계열용이라는 뜻입니다. Rocky Linux 9, AlmaLinux 9, RHEL 9에 설치할 수 있습니다.

### 설치되는 파일들

패키지를 설치하면 다음 위치에 파일이 놓입니다. 나중에 뭘 고쳐야 할지 헷갈릴 때 참고하세요.

| 경로 | 설명 |
|---|---|
| `/usr/sbin/haproxy` | HAProxy 실행 파일 |
| `/etc/haproxy/haproxy.cfg` | **가장 중요한 설정 파일.** 대부분의 작업은 여기서 합니다. |
| `/etc/haproxy/errors/` | 오류 응답 HTML (400, 403, 500, 502, 503, 504 등) |
| `/usr/share/haproxy/examples/` | **설정 예제 파일 모음.** 아래 [설정 예제 모음](#설정-예제-모음)의 내용이 그대로 파일로 들어 있습니다 |
| `/usr/lib/systemd/system/haproxy.service` | systemd 서비스 정의 |
| `/etc/rsyslog.d/49-haproxy.conf` | 로그를 파일로 떨구는 rsyslog 규칙 |
| `/etc/logrotate.d/haproxy` | 로그 자동 정리 규칙 (매일, 14일 보관) |
| `/var/log/haproxy/` | 로그가 쌓이는 곳 |
| `/var/lib/haproxy/` | 보안 격리(chroot)용 빈 디렉터리 |
| `/usr/bin/halog` | 로그 분석 도구 |
| `/usr/bin/iprange` | IP 대역 계산 도구 |

### 어떤 기능이 켜져 있나요

기본 빌드에는 실무에서 흔히 쓰는 기능이 켜져 있습니다. 설치 후 `haproxy -vv` 명령으로 언제든 확인할 수 있습니다.

- **SSL/TLS** — OpenSSL 3.x 연동 (HTTPS 처리)
- **압축** — zlib (gzip, deflate 응답 압축)
- **정규식** — PCRE2 + JIT 가속
- **멀티스레드** — 기본 64스레드, 최대 1024스레드
- **투명 프록시**, **TCP Fast Open**, **네트워크 네임스페이스**
- **ACME** — 인증서 자동 발급 (HAProxy 3.x 신규 기능)

Lua 스크립트와 Prometheus 지표는 기본으로 꺼져 있고, 필요하면 [빌드 옵션](#빌드-옵션)에서 켤 수 있습니다.

---

## 빌드 준비하기

빌드 방법은 두 가지이고, 둘 중 **하나만** 고르면 됩니다.

**Docker 방식**을 권장합니다. 빌드에 필요한 컴파일러와 라이브러리가 전부 컨테이너 안에서만 설치되고 끝나기 때문에, 여러분의 서버는 조금도 더러워지지 않습니다. 또 어느 컴퓨터에서 돌리든 항상 Rocky Linux 9 환경에서 빌드되므로 결과물이 늘 똑같습니다. 노트북(맥이든 윈도우든 리눅스든)에서 빌드해서 RPM만 서버로 옮기는 것도 가능합니다.

**직접 빌드 방식**은 Docker를 쓸 수 없는 환경일 때 선택합니다. 이 경우 빌드하는 서버 자체가 RHEL 9 계열이어야 하고, 개발 도구 수십 개가 그 서버에 설치됩니다. 운영 서버에서는 권장하지 않습니다.

두 방식 모두 빌드 도중 `haproxy.org`에서 소스 코드를 내려받으므로 **인터넷 연결이 필요합니다.**

---

## 방법 1 — Docker로 빌드하기 (권장)

Docker가 설치되어 있는지 먼저 확인합니다.

```bash
docker --version
```

그다음 저장소를 받아서 빌드합니다.

```bash
git clone https://github.com/DataDynamics/haproxy3-rpm-builder-internal.git
cd haproxy3-rpm-builder-internal
make run-docker
```

이 한 줄이 실제로는 세 가지 일을 순서대로 합니다. 먼저 Rocky Linux 9 기반으로 컴파일러가 들어 있는 빌더 이미지를 만들고, 그 컨테이너 안에서 HAProxy 소스를 받아 컴파일한 뒤, 완성된 RPM을 여러분 컴퓨터의 `RPMS/` 디렉터리로 복사해 줍니다.

처음 실행하면 Rocky Linux 이미지를 내려받고 개발 도구를 설치하느라 **5~10분쯤** 걸립니다. 두 번째부터는 이미지가 캐시되어 훨씬 빠릅니다.

끝나면 결과를 확인합니다.

```bash
ls -lh RPMS/
```

---

## 방법 2 — 서버에서 직접 빌드하기

이 방법은 **RHEL 9 계열 서버에서만** 동작합니다. 먼저 빌드에 필요한 도구를 설치합니다.

```bash
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y openssl-devel zlib-devel systemd-rpm-macros pcre2-devel \
                    rpm-build redhat-rpm-config wget
```

그다음 빌드합니다.

```bash
git clone https://github.com/DataDynamics/haproxy3-rpm-builder-internal.git
cd haproxy3-rpm-builder-internal
make
```

Docker 방식과 달리 결과물이 `RPMS/`가 아니라 아래 경로에 생깁니다. 헷갈리기 쉬우니 주의하세요.

```bash
ls -lh rpmbuild/RPMS/x86_64/
```

> **참고** — `make`는 기본적으로 `sudo` 없이 동작합니다(`NO_SUDO=1`이 기본값). 일반 사용자 권한으로 빌드하다가 권한 문제가 생기면 `make NO_SUDO=0`으로 각 단계에 `sudo`를 붙일 수 있습니다.

---

## 빌드 옵션

옵션은 `make` 뒤에 `이름=값` 형태로 붙입니다. 예를 들어 Lua를 켜려면 `make run-docker USE_LUA=1`처럼 씁니다.

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `MAINVERSION` | `3.4` | HAProxy 계열 버전. 다운로드 경로를 결정합니다. |
| `VERSION` | `3.4.3` | 정확한 HAProxy 버전 |
| `RELEASE` | `1` | 패키지 릴리스 번호. 같은 HAProxy 버전으로 패키지를 다시 만들 때 올립니다. |
| `USE_LUA` | `0` | Lua 스크립트 지원 |
| `USE_PROMETHEUS` | `0` | Prometheus 지표 노출 기능 |
| `NO_SUDO` | `1` | `1`이면 sudo 없이, `0`이면 각 명령에 sudo를 붙여 실행 |

### Lua 지원 켜기

```bash
make run-docker USE_LUA=1
```

Lua를 켜면 HAProxy 설정 안에서 Lua 스크립트를 실행할 수 있습니다. 복잡한 요청 라우팅 규칙이나 커스텀 인증 로직처럼, 기본 설정 문법만으로는 표현하기 어려운 처리를 직접 코드로 짤 때 씁니다. 빌드 과정에서 Lua 5.4.7을 소스로 함께 컴파일하므로 시간이 몇 분 더 걸립니다.

### Prometheus 지표 켜기

```bash
make run-docker USE_PROMETHEUS=1
```

Prometheus나 Grafana로 HAProxy를 모니터링한다면 이 옵션을 켜세요. 켜고 나면 설정 파일에 아래처럼 추가해서 지표 수집 주소를 열어 줄 수 있습니다.

```
frontend metrics
  bind :8405
  http-request use-service prometheus-exporter if { path /metrics }
```

이제 `http://<서버주소>:8405/metrics` 에서 Prometheus가 읽을 수 있는 형식의 지표가 나옵니다. 사람이 눈으로 보는 용도라면 [통계 페이지](#통계stats-페이지)가 더 편하고, 장기 추세를 저장하고 알림을 걸려면 Prometheus 쪽이 맞습니다.

두 옵션을 함께 켜는 것도 됩니다.

```bash
make run-docker USE_LUA=1 USE_PROMETHEUS=1
```

---

## 설치하고 실행하기

만들어진 RPM을 대상 서버로 옮긴 뒤 설치합니다.

```bash
sudo dnf install -y ./haproxy-3.4.3-1.el9.x86_64.rpm
```

`dnf`는 필요한 라이브러리(OpenSSL, zlib, PCRE2, rsyslog)를 알아서 함께 설치해 줍니다. 설치가 잘 됐는지 버전을 확인해 봅니다.

```bash
haproxy -v
```

서비스를 시작하고 부팅 시 자동 시작되도록 등록합니다. `--now`가 "지금 바로 시작"이고 `enable`이 "부팅할 때도 시작"입니다.

```bash
sudo systemctl enable --now haproxy
sudo systemctl status haproxy
```

`active (running)`이 보이면 정상입니다.

설정을 바꾼 뒤에는 **먼저 문법 검사부터** 하는 습관을 들이세요. 잘못된 설정으로 재시작하면 서비스가 내려간 채 안 올라옵니다.

```bash
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
```

아무 메시지 없이 끝나면 이상이 없다는 뜻입니다. 검사를 통과했다면 **재시작(restart)이 아니라 리로드(reload)** 를 쓰세요. 리로드는 기존 연결을 끊지 않고 설정만 새로 적용합니다.

```bash
sudo systemctl reload haproxy
```

방화벽이 켜져 있다면 사용할 포트를 열어 줘야 합니다.

```bash
sudo firewall-cmd --permanent --add-port=9000/tcp   # 통계 페이지
sudo firewall-cmd --reload
```

---

## 통계(Stats) 페이지

HAProxy에는 **웹 브라우저로 열어 보는 실시간 상태 화면**이 내장되어 있습니다. 별도 프로그램을 설치할 필요 없이, 지금 트래픽이 얼마나 들어오는지 · 어느 백엔드 서버가 죽었는지 · 오류가 얼마나 나는지를 한눈에 볼 수 있습니다. 장애가 났을 때 가장 먼저 열어 보게 되는 화면입니다.

### 접속하기

이 패키지는 통계 페이지가 **처음부터 켜진 채로** 설치됩니다. 서비스를 시작한 뒤 브라우저에서 아래 주소로 들어가면 됩니다.

```
http://<서버주소>:9000/haproxy_stats
```

터미널에서 바로 확인해 볼 수도 있습니다.

```bash
curl -s http://127.0.0.1:9000/haproxy_stats | head
```

화면이 안 뜬다면 대부분 방화벽 때문입니다. 위 [설치하고 실행하기](#설치하고-실행하기)의 `firewall-cmd` 명령으로 9000 포트를 열어 주세요.

### 화면 읽는 법

접속하면 표가 여러 개 나옵니다. 각 표가 설정 파일에 정의한 프록시 하나에 해당하고, 표 안의 행은 프론트엔드(들어오는 쪽), 백엔드(나가는 쪽), 그리고 개별 서버를 나타냅니다. 주요 열은 다음과 같습니다.

| 열 이름 | 의미 |
|---|---|
| **Status** | 가장 중요합니다. `UP`은 정상, `DOWN`은 헬스체크 실패, `OPEN`은 요청을 받는 중이라는 뜻입니다. |
| **Sessions — Cur / Max / Limit** | 현재 연결 수 / 지금까지 최고치 / 허용 한계. Cur가 Limit에 근접하면 증설을 검토할 때입니다. |
| **Session rate — Cur / Max** | 초당 새 연결 수. 트래픽 급증을 감지할 때 봅니다. |
| **Bytes — In / Out** | 주고받은 총 바이트 |
| **Denied — Req / Resp** | 설정한 규칙에 걸려 차단된 요청·응답 수 |
| **Errors — Req / Conn / Resp** | 잘못된 요청, 백엔드 연결 실패, 응답 오류 수. 여기 숫자가 올라가면 원인을 찾아야 합니다. |
| **Warnings — Retr / Redis** | 재시도 횟수와 다른 서버로 넘긴 횟수. 특정 서버가 불안정할 때 늘어납니다. |
| **LastChk** | 마지막 헬스체크 결과 |

행 색깔로도 상태를 알 수 있습니다. **초록색**은 정상, **노란색**은 헬스체크 진행 중이거나 경고 상태, **빨간색**은 다운, **회색**은 관리자가 의도적으로 내려 둔(maintenance) 상태입니다.

### 보안 — 꼭 읽어 주세요

> ⚠️ **기본 설정의 통계 페이지에는 비밀번호가 걸려 있지 않습니다.**

이 저장소가 제공하는 `haproxy.cfg`는 설정 파일 첫 줄에도 적혀 있듯 **테스트용 샘플**입니다. 통계 페이지는 서버 이름, 내부 구조, 트래픽 규모 같은 정보를 그대로 노출하므로, 인터넷에 열린 서버라면 **운영에 쓰기 전에 반드시** 아래 조치 중 하나를 하세요.

**첫째, 비밀번호 걸기.** 가장 간단한 방법입니다. `/etc/haproxy/haproxy.cfg`의 `listen stats` 부분에 `stats auth` 한 줄을 추가합니다.

```
listen stats
  bind :9000
  mode http
  stats enable
  stats realm Haproxy\ Statistics
  stats uri /haproxy_stats
  stats auth admin:여기에_강력한_비밀번호
```

**둘째, 접속 가능한 주소 제한.** 아예 내부망에서만 열리게 하는 편이 더 안전합니다. `bind` 주소를 내부 IP로 못 박거나, 접근 제어 규칙을 겁니다.

```
listen stats
  bind 10.0.0.5:9000              # 내부 인터페이스에만 바인딩
  mode http
  stats enable
  stats uri /haproxy_stats
  acl allowed_net src 10.0.0.0/8 192.168.0.0/16
  http-request deny if !allowed_net
```

**셋째, URL 바꾸기.** 이것만으로 보안이 되지는 않지만, 자동화된 스캐너에 걸릴 확률은 줄어듭니다. `stats uri` 값을 추측하기 어려운 문자열로 바꾸면 됩니다.

수정 후에는 반드시 문법 검사와 리로드를 하세요.

```bash
sudo haproxy -c -f /etc/haproxy/haproxy.cfg && sudo systemctl reload haproxy
```

### 관리자 기능 켜기

`stats admin` 을 추가하면 통계 화면에서 **버튼으로 서버를 내리고 올릴 수 있습니다.** 서버를 점검할 때 트래픽만 잠시 빼 두는 용도로 아주 편리합니다. 다만 브라우저에서 서비스를 중단시킬 수 있다는 뜻이므로, 반드시 인증과 함께 쓰고 신뢰할 수 있는 네트워크에서만 여세요.

```
  stats auth admin:강력한_비밀번호
  stats admin if TRUE
```

### 포트와 경로 바꾸기

9000번 포트가 이미 쓰이고 있다면 `bind` 뒤의 숫자를, 접속 경로를 바꾸려면 `stats uri` 값을 고치면 됩니다.

```
listen stats
  bind :8404                       # 포트 변경
  stats uri /my_secret_stats_path  # 경로 변경
```

### 명령줄에서 확인하기 (관리 소켓)

브라우저 대신 터미널에서 같은 정보를 볼 수도 있습니다. HAProxy는 `/run/haproxy/haproxy.sock` 에 관리용 소켓을 열어 두는데, `socat`으로 명령을 보내면 됩니다. 모니터링 스크립트를 짤 때 유용합니다.

```bash
sudo dnf install -y socat

echo "show stat" | sudo socat stdio /run/haproxy/haproxy.sock   # 통계 (CSV 형식)
echo "show info" | sudo socat stdio /run/haproxy/haproxy.sock   # 프로세스 정보
echo "show servers state" | sudo socat stdio /run/haproxy/haproxy.sock
```

이 소켓은 `level admin` 권한으로 열려 있어서 서버를 내리고 올리는 것도 가능합니다. 파일 권한이 `600`이라 root만 접근할 수 있습니다.

---

## 설정 파일 이해하기

거의 모든 작업은 `/etc/haproxy/haproxy.cfg` 한 파일에서 이루어집니다. 이 패키지가 넣어 주는 기본 설정은 크게 세 덩어리로 되어 있습니다.

**`global`** 은 HAProxy 프로세스 전체에 적용되는 설정입니다. 어떤 계정으로 실행할지(`user`, `group`), 어디에 격리시킬지(`chroot`), 로그를 어디로 보낼지, 관리 소켓을 어디에 열지 같은 것을 정합니다. 여기 값들은 프로세스를 완전히 재시작해야 반영되는 경우가 많습니다.

**`defaults`** 는 뒤따라 나오는 모든 프록시가 **공통으로 물려받는 기본값**입니다. 타임아웃이나 로그 형식처럼 매번 반복해서 쓰기 번거로운 설정을 여기 한 번만 적어 둡니다.

> 순서가 중요합니다. `defaults`는 **자기 뒤에 나오는** 섹션에만 적용됩니다. `defaults`를 파일 맨 아래에 두면 위쪽 프록시들이 타임아웃을 물려받지 못해 경고가 뜨고, 실제로 연결이 무한정 매달릴 수 있습니다.

**`listen`** (또는 `frontend` + `backend`)은 실제로 트래픽을 처리하는 부분입니다. 기본 설정에는 통계 페이지용 `listen stats` 하나만 들어 있습니다. `listen`은 프론트엔드와 백엔드를 한 덩어리로 합쳐 쓰는 간편 문법이고, 규모가 커지면 `frontend`와 `backend`로 나누어 쓰는 편이 관리하기 좋습니다.

실제로 트래픽을 처리하려면 `listen`이나 `frontend`/`backend`를 직접 써 주어야 합니다. 바로 다음 [설정 예제 모음](#설정-예제-모음)에 용도별로 정리해 두었으니 필요한 것을 골라 쓰세요.

### 부하 분산의 기본 형태

가장 단순한 예부터 보겠습니다. 아래 내용을 설정 파일 끝에 덧붙이면 웹 서버 두 대로 트래픽이 나뉩니다.

```
frontend web
  bind :80
  default_backend web_servers

backend web_servers
  balance roundrobin
  option httpchk GET /health
  server web1 10.0.0.11:8080 check
  server web2 10.0.0.12:8080 check
```

`frontend web`은 80번 포트로 들어오는 요청을 받아 `backend web_servers`로 넘깁니다. `balance roundrobin`은 두 서버에 번갈아 나눠 준다는 뜻이고, `check`가 붙은 서버는 HAProxy가 주기적으로 `/health` 경로를 호출해 살아 있는지 확인합니다. 죽은 서버는 자동으로 제외되며, 그 상태가 통계 페이지에 빨간색으로 표시됩니다.

늘 그렇듯 저장한 뒤에는 검사하고 리로드하세요.

```bash
sudo haproxy -c -f /etc/haproxy/haproxy.cfg && sudo systemctl reload haproxy
```

---

## 설정 예제 모음

실무에서 자주 쓰는 설정을 용도별로 모았습니다. **필요한 것만 골라서** `/etc/haproxy/haproxy.cfg` 끝에 붙여 넣고, IP 주소와 포트만 환경에 맞게 바꾸면 됩니다.

> 이 문서의 모든 예제는 HAProxy 3.4.3에서 문법 검사(`haproxy -c`)를 **경고 없이** 통과하는 것을 확인했습니다. 웹·라우팅·세션 고정·HTTPS·TCP·속도 제한 예제는 실제 백엔드를 붙여 동작까지 검증했습니다.

### 예제는 파일로도 설치됩니다

아래 예제들은 패키지에 **파일로 함께 들어 있습니다.** 문서를 보며 옮겨 적을 필요 없이 `/usr/share/haproxy/examples/`에서 바로 꺼내 쓰면 됩니다. 각 파일 맨 위 주석에 무엇을 준비해야 하고 어떤 값을 고쳐야 하는지가 적혀 있습니다.

```bash
ls /usr/share/haproxy/examples/
cat /usr/share/haproxy/examples/README.txt      # 전체 목록과 사용법
```

| 파일 | 아래 예제 |
|---|---|
| `01-web-http-lb.cfg` | [1. 웹 서버 부하 분산](#1-웹-서버-부하-분산-http) |
| `02-real-client-ip.cfg` | [2. 진짜 접속자 IP 알려주기](#2-백엔드에-진짜-접속자-ip-알려주기) |
| `03-https-offload.cfg` | [3. HTTPS 처리 (SSL 종료)](#3-https-처리-ssl-종료) |
| `04-http2.cfg` | [4. HTTP/2 사용하기](#4-http2-사용하기) |
| `05-routing-acl.cfg` | [5. 경로·도메인별 라우팅](#5-경로도메인별로-다른-서버에-보내기) |
| `06-sticky-session.cfg` | [6. 세션 고정](#6-세션-고정-sticky-session) |
| `07-mysql.cfg` | [7. MySQL / MariaDB](#mysql--mariadb) |
| `08-mysql-rw-split.cfg` | [7. MySQL 쓰기·읽기 분리](#mysql--mariadb) |
| `09-postgresql.cfg` | [7. PostgreSQL](#postgresql) |
| `10-redis.cfg` | [7. Redis](#redis) |
| `11-tcp-passthrough.cfg` | [8. 일반 TCP 서비스 중계](#8-일반-tcp-서비스-중계) |
| `12-rate-limit.cfg` | [9. 접속 제한과 속도 제한](#9-접속-제한과-속도-제한) |
| `13-maintenance.cfg` | [10. 서버 점검 처리](#10-서버-점검maintenance-처리) |

**붙여 넣기 전에 예제만 따로 검사해 볼 수도 있습니다.** 예제 파일에는 `frontend`/`backend`/`listen` 블록만 들어 있어(그래야 통째로 복사할 수 있으니까요) 그대로는 검사할 수 없는데, 같은 디렉터리의 `00-base.cfg`가 `global`/`defaults` 자리를 채워 줍니다. 도우미 스크립트가 이걸 대신 해 줍니다.

```bash
/usr/share/haproxy/examples/check-example.sh 01-web-http-lb.cfg   # 하나만
/usr/share/haproxy/examples/check-example.sh --all                # 전부
```

> `03`·`04`번은 인증서 파일이 실제로 있어야 검사를 통과합니다. 만드는 방법은 [3번 예제](#3-https-처리-ssl-종료)와 해당 파일 주석에 있습니다.
>
> 이 디렉터리의 파일은 패키지를 업그레이드하면 최신 내용으로 교체됩니다. 고쳐 쓸 내용은 `/etc/haproxy/haproxy.cfg`에 옮겨 두세요.

### 예제를 적용하는 공통 절차

어떤 예제든 적용 방법은 똑같습니다. 이 세 단계를 습관으로 만드세요.

```bash
sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.bak   # 1. 백업
sudo vi /etc/haproxy/haproxy.cfg                                 # 2. 예제 붙여 넣고 IP 수정
sudo haproxy -c -f /etc/haproxy/haproxy.cfg && sudo systemctl reload haproxy   # 3. 검사 후 반영
```

3단계에서 `&&`로 이어 둔 것이 중요합니다. 문법 검사가 실패하면 리로드가 아예 실행되지 않으므로, 잘못된 설정이 서비스에 반영되는 사고를 막아 줍니다.

설치된 예제 파일을 쓴다면 2단계에서 직접 옮겨 적는 대신 파일을 이어 붙이면 됩니다.

```bash
sudo sh -c 'cat /usr/share/haproxy/examples/01-web-http-lb.cfg >> /etc/haproxy/haproxy.cfg'
sudo vi /etc/haproxy/haproxy.cfg   # IP·포트만 수정
```

**예제를 여러 개 붙여 넣을 때는 이름과 포트가 겹치지 않는지 확인하세요.** 여러 예제가 `frontend web` / `backend web_servers`라는 같은 이름과 `:80` 포트를 쓰고 있습니다. 겹치면 HAProxy가 시작되지 않습니다. 또 `defaults`는 자기 뒤에 나오는 섹션에만 적용되므로 예제는 항상 파일 **끝**에 붙여야 합니다.

### 부하 분산 알고리즘 고르기

`balance` 뒤에 오는 값이 트래픽을 나누는 방식을 정합니다. 상황에 맞는 것을 고르세요.

| 알고리즘 | 동작 | 언제 쓰나 |
|---|---|---|
| `roundrobin` | 차례대로 돌아가며 배분 | 서버 성능이 비슷한 일반 웹 서버. **가장 무난한 기본값** |
| `leastconn` | 연결 수가 가장 적은 서버로 | 데이터베이스처럼 연결이 오래 유지되는 서비스 |
| `source` | 접속자 IP를 해시해 항상 같은 서버로 | 쿠키를 못 쓰는 환경에서 세션을 고정할 때 |
| `first` | 살아 있는 첫 번째 서버에 몰아주기 | Redis처럼 마스터 한 대만 써야 할 때 |
| `uri` | 요청 URL을 해시해 배분 | 캐시 서버. 같은 URL은 늘 같은 서버로 가야 적중률이 오릅니다 |

---

### 1. 웹 서버 부하 분산 (HTTP)

가장 기본이 되는 형태입니다. 여러 대의 웹 서버(WAS)에 요청을 나눠 주고, 죽은 서버는 자동으로 빼 줍니다.

```
frontend web
  bind :80
  default_backend web_servers

backend web_servers
  balance roundrobin
  option httpchk GET /health
  http-check expect status 200
  server web1 10.0.0.11:8080 check
  server web2 10.0.0.12:8080 check
```

`option httpchk GET /health`는 헬스체크 방법을 정합니다. HAProxy가 각 서버의 `/health` 경로를 주기적으로 호출하고, `http-check expect status 200`에 따라 200이 돌아올 때만 정상으로 봅니다.

여기서 **헬스체크 경로를 잘 고르는 것이 중요합니다.** `/` 같은 무거운 페이지 대신, DB 연결 상태 정도만 확인하고 바로 200을 돌려주는 가벼운 전용 경로를 애플리케이션에 만들어 두는 편이 좋습니다. 헬스체크는 기본적으로 2초마다 호출되므로 무거운 경로를 쓰면 그 자체가 부하가 됩니다.

체크 간격을 조정하려면 `check` 뒤에 옵션을 붙입니다.

```
  server web1 10.0.0.11:8080 check inter 5s fall 3 rise 2
```

`inter 5s`는 5초마다 검사, `fall 3`은 3회 연속 실패해야 죽은 것으로 판정, `rise 2`는 2회 연속 성공해야 다시 살리는 것으로 봅니다. 순간적인 네트워크 불안정으로 서버가 들락날락하는 것을 막아 줍니다.

### 2. 백엔드에 진짜 접속자 IP 알려주기

부하 분산을 걸면 웹 서버 입장에서는 모든 요청이 HAProxy에서 온 것처럼 보입니다. 접속자의 실제 IP를 알려면 `option forwardfor`를 넣어야 합니다.

```
backend web_servers
  balance roundrobin
  option forwardfor
  server web1 10.0.0.11:8080 check
```

이러면 `X-Forwarded-For` 헤더에 원래 접속자 IP가 담겨 전달됩니다. 애플리케이션(또는 그 앞의 Nginx/Tomcat)에서 이 헤더를 신뢰하도록 설정해 주어야 로그에 제대로 찍힙니다.

### 3. HTTPS 처리 (SSL 종료)

HAProxy가 HTTPS를 대신 처리하고 뒤쪽 서버와는 평문 HTTP로 통신하는 방식입니다. 인증서를 한 곳에서만 관리하면 되므로 가장 널리 쓰입니다.

```
frontend web
  bind :80
  bind :443 ssl crt /etc/haproxy/certs/example.com.pem
  http-request redirect scheme https code 301 unless { ssl_fc }
  http-response set-header Strict-Transport-Security "max-age=31536000"
  default_backend web_servers

backend web_servers
  balance roundrobin
  option forwardfor
  http-request set-header X-Forwarded-Proto https if { ssl_fc }
  server web1 10.0.0.11:8080 check
  server web2 10.0.0.12:8080 check
```

`http-request redirect ... unless { ssl_fc }` 한 줄이 **HTTP로 들어온 요청을 자동으로 HTTPS로 돌려보냅니다.** `ssl_fc`는 "이 연결이 SSL이냐"를 뜻하므로, SSL이 아닐 때만 리다이렉트가 걸립니다.

> `code 301`을 빼면 **302(임시 이동)** 로 응답합니다. HTTP를 영구히 닫을 생각이라면 301을 명시하세요. 브라우저가 결과를 캐시하므로, 되돌릴 여지를 남겨 두고 싶다면 오히려 302가 안전합니다.

`X-Forwarded-Proto https` 헤더는 뒤쪽 애플리케이션에게 "원래는 HTTPS 요청이었다"고 알려 줍니다. 이게 없으면 애플리케이션이 만드는 링크가 `http://`로 나가서 무한 리다이렉트가 생기는 일이 흔합니다.

**인증서 파일 준비하기.** HAProxy는 인증서와 개인키를 **한 파일에 합쳐서** 넣어야 합니다. Let's Encrypt를 쓴다면 이렇게 만듭니다.

```bash
sudo mkdir -p /etc/haproxy/certs
sudo cat /etc/letsencrypt/live/example.com/fullchain.pem \
         /etc/letsencrypt/live/example.com/privkey.pem \
         > /etc/haproxy/certs/example.com.pem
sudo chmod 600 /etc/haproxy/certs/example.com.pem
```

여러 도메인을 쓴다면 `crt` 뒤에 파일 대신 **디렉터리**를 지정하면 됩니다. HAProxy가 그 안의 인증서를 모두 읽어 SNI로 알아서 골라 씁니다.

```
  bind :443 ssl crt /etc/haproxy/certs/
```

### 4. HTTP/2 사용하기

`alpn h2,http/1.1`을 붙이면 HTTP/2를 지원하는 브라우저와는 HTTP/2로, 아니면 HTTP/1.1로 통신합니다.

```
frontend web
  bind :443 ssl crt /etc/haproxy/certs/example.com.pem alpn h2,http/1.1
  default_backend web_servers

backend web_servers
  balance roundrobin
  server web1 10.0.0.11:8080 check
  server web2 10.0.0.12:8443 check ssl verify none alpn h2
```

백엔드 쪽 `server` 줄의 `ssl verify none alpn h2`는 HAProxy와 뒤쪽 서버 사이도 HTTPS/HTTP2로 연결한다는 뜻입니다. 내부망이라 인증서 검증이 필요 없을 때 `verify none`을 씁니다. 인터넷을 거친다면 `verify required`와 `ca-file`을 제대로 지정하세요.

### 5. 경로·도메인별로 다른 서버에 보내기

한 대의 HAProxy로 여러 서비스를 나눠 받는 방법입니다. `acl`로 조건에 이름을 붙이고 `use_backend`로 연결합니다.

```
frontend web
  bind :80
  acl is_api      path_beg /api
  acl is_static   path_beg /static /images
  acl is_admin    hdr(host) -i admin.example.com
  use_backend api_servers    if is_api
  use_backend static_servers if is_static
  use_backend admin_servers  if is_admin
  default_backend web_servers

backend api_servers
  balance leastconn
  server api1 10.0.0.21:8080 check

backend static_servers
  balance roundrobin
  server st1 10.0.0.31:80 check

backend admin_servers
  server adm1 10.0.0.41:8080 check

backend web_servers
  server web1 10.0.0.11:8080 check
```

`path_beg /api`는 "경로가 /api로 시작하면", `hdr(host) -i admin.example.com`은 "Host 헤더가 이 도메인이면"이라는 뜻입니다(`-i`는 대소문자 무시). 어느 조건에도 안 걸리면 `default_backend`로 갑니다.

**규칙은 위에서부터 순서대로 평가되고 먼저 맞는 것이 이깁니다.** 그러니 범위가 좁은 조건을 위에, 넓은 조건을 아래에 두세요.

자주 쓰는 조건은 다음과 같습니다.

| 조건 | 의미 |
|---|---|
| `path_beg /api` | 경로가 `/api`로 시작 |
| `path_end .jpg .png` | 경로가 해당 확장자로 끝남 |
| `hdr(host) -i example.com` | Host 헤더가 일치 |
| `hdr_beg(host) -i api.` | Host가 `api.`로 시작 (서브도메인) |
| `src 10.0.0.0/8` | 접속자 IP가 해당 대역 |
| `method POST` | HTTP 메서드가 POST |

### 6. 세션 고정 (sticky session)

로그인 상태를 서버 메모리에 들고 있는 애플리케이션이라면, 같은 사용자를 계속 같은 서버로 보내야 합니다. HAProxy가 쿠키를 심어서 처리해 줍니다.

```
backend web_servers
  balance roundrobin
  cookie SRVID insert indirect nocache
  server web1 10.0.0.11:8080 check cookie web1
  server web2 10.0.0.12:8080 check cookie web2
```

`cookie SRVID insert`는 HAProxy가 `SRVID`라는 쿠키를 직접 만들어 응답에 넣는다는 뜻이고, 각 `server` 줄 끝의 `cookie web1`이 그 쿠키에 담길 값입니다. 브라우저가 이 쿠키를 다시 보내면 HAProxy가 그 값을 보고 원래 서버로 되돌려 줍니다. `indirect nocache`는 이 쿠키가 애플리케이션에 전달되지 않게 하고 중간 캐시에 저장되지 않게 막는 안전장치입니다.

> 세션 고정은 편리하지만 **부하가 고르게 나뉘지 않는 부작용**이 있습니다. 한 서버가 죽으면 그 서버에 묶여 있던 사용자는 로그인이 풀립니다. 가능하다면 세션을 Redis 같은 외부 저장소로 빼서 세션 고정 자체가 필요 없게 만드는 편이 근본적인 해법입니다.

쿠키를 쓸 수 없는 환경(예: TCP 모드)에서는 접속자 IP 기준으로 고정할 수 있습니다.

```
backend web_servers
  balance source
  server web1 10.0.0.11:8080 check
  server web2 10.0.0.12:8080 check
```

---

### 7. 데이터베이스 부하 분산

데이터베이스는 HTTP가 아니므로 반드시 **`mode tcp`** 로 동작시켜야 합니다. 그리고 웹과 달리 연결이 오래 유지되므로 **타임아웃을 넉넉히** 잡아야 합니다. 기본값인 50초를 그대로 쓰면 조금 긴 쿼리가 도중에 끊깁니다.

#### MySQL / MariaDB

읽기 부하를 복제 서버로 분산하는 구성입니다.

```
listen mysql
  bind :3306
  mode tcp
  option tcplog
  balance leastconn
  timeout client 600s
  timeout server 600s
  option mysql-check user haproxy_check
  server db1 10.0.0.21:3306 check
  server db2 10.0.0.22:3306 check backup
```

`option mysql-check`를 쓰려면 **DB에 전용 점검 계정을 먼저 만들어 두어야 합니다.** 비밀번호 없이 접속만 되면 되고 아무 권한도 줄 필요가 없습니다.

```sql
CREATE USER 'haproxy_check'@'10.0.0.%';
```

`db2`에 붙은 `backup`은 "평소에는 쓰지 말고 앞의 서버가 모두 죽었을 때만 쓰라"는 뜻입니다. **쓰기(master)와 읽기(replica)를 구분해야 한다면 이 구성만으로는 부족합니다.** 쓰기용 포트와 읽기용 포트를 따로 열어 주세요.

```
listen mysql_write
  bind :3306
  mode tcp
  option tcplog
  timeout client 600s
  timeout server 600s
  option mysql-check user haproxy_check
  server master 10.0.0.21:3306 check
  server standby 10.0.0.22:3306 check backup

listen mysql_read
  bind :3307
  mode tcp
  option tcplog
  balance roundrobin
  timeout client 600s
  timeout server 600s
  option mysql-check user haproxy_check
  server replica1 10.0.0.22:3306 check
  server replica2 10.0.0.23:3306 check
```

애플리케이션에서 쓰기는 3306, 읽기는 3307로 접속하도록 나누면 됩니다.

#### PostgreSQL

방식은 MySQL과 같고 점검 옵션만 다릅니다.

```
listen postgresql
  bind :5432
  mode tcp
  option tcplog
  balance leastconn
  timeout client 600s
  timeout server 600s
  option pgsql-check user haproxy_check
  server pg1 10.0.0.21:5432 check
  server pg2 10.0.0.22:5432 check backup
```

점검 계정을 만들고 접속을 허용해 주어야 합니다.

```sql
CREATE ROLE haproxy_check LOGIN;
```

`pg_hba.conf`에도 이 계정이 접속할 수 있도록 한 줄 추가해야 합니다.

#### Redis

Redis는 마스터 한 대에만 써야 하므로, **마스터를 자동으로 찾아내는** 헬스체크를 씁니다.

```
listen redis
  bind :6379
  mode tcp
  option tcplog
  balance first
  option tcp-check
  tcp-check send PING\r\n
  tcp-check expect string +PONG
  tcp-check send info\ replication\r\n
  tcp-check expect string role:master
  tcp-check send QUIT\r\n
  tcp-check expect string +OK
  server redis1 10.0.0.31:6379 check inter 1s
  server redis2 10.0.0.32:6379 check inter 1s
```

`tcp-check`가 실제로 Redis에 접속해서 `PING`을 보내고 `+PONG`을 확인한 뒤, `INFO replication` 결과에 `role:master`가 있는지까지 봅니다. 복제(slave) 서버는 이 검사를 통과하지 못하므로 자동으로 제외됩니다. 장애 조치(failover)로 마스터가 바뀌면 HAProxy가 알아서 새 마스터로 트래픽을 옮깁니다.

`send` 줄의 `\r\n`과 `info\ replication`의 백슬래시는 문법상 반드시 필요하니 그대로 적어 주세요.

---

### 8. 일반 TCP 서비스 중계

HTTP가 아닌 서비스(메일, SSH, 사설 프로토콜 등)는 `mode tcp`로 그대로 흘려보내면 됩니다.

```
listen smtp
  bind :25
  mode tcp
  option tcplog
  balance roundrobin
  option tcp-check
  server mail1 10.0.0.41:25 check
  server mail2 10.0.0.42:25 check
```

`option tcp-check`만 쓰면 **포트가 열려 있는지만** 확인합니다. 더 정확히 보고 싶다면 실제로 주고받는 문자열을 지정할 수 있습니다.

```
  option tcp-check
  tcp-check expect string 220
```

메일 서버가 접속 시 보내는 `220` 인사말을 확인하는 식입니다.

> `mode tcp`에서는 `option httplog`를 쓰면 안 됩니다. HTTP 정보가 없어 로그가 비어 보입니다. 예제처럼 `option tcplog`로 바꿔 주세요. `defaults`에 `mode http`가 있어도 각 섹션에서 `mode tcp`로 덮어쓰면 됩니다.

---

### 9. 접속 제한과 속도 제한

특정 IP에서 짧은 시간에 과도한 요청이 오면 차단하는 설정입니다. 단순한 크롤러나 무차별 로그인 시도를 막는 데 효과적입니다.

```
frontend web
  bind :80
  stick-table type ip size 100k expire 30s store http_req_rate(10s)
  http-request track-sc0 src
  http-request deny deny_status 429 if { sc_http_req_rate(0) gt 100 }
  acl allowed_net src 10.0.0.0/8 192.168.0.0/16
  http-request deny if { path_beg /admin } !allowed_net
  default_backend web_servers

backend web_servers
  server web1 10.0.0.11:8080 check maxconn 200
```

`stick-table`은 IP별 요청 횟수를 기억하는 표입니다. `http_req_rate(10s)`는 최근 10초간의 요청 수를 세고, 그 값이 100을 넘으면 `429 Too Many Requests`로 거절합니다. 30초간 요청이 없으면 기록이 지워집니다.

그 아래 두 줄은 `/admin` 경로를 내부망에서만 열어 주는 설정입니다. 관리자 페이지를 외부에 노출하지 않는 간단하고 확실한 방법입니다.

`server` 줄의 `maxconn 200`은 그 서버가 동시에 처리할 연결 수를 제한합니다. 백엔드가 감당할 수 있는 수준을 넘어서면 HAProxy가 대기시켜 주므로, 트래픽 폭주로 서버가 통째로 넘어가는 것을 막아 줍니다.

> 임계값은 서비스 성격에 따라 크게 다릅니다. 처음에는 넉넉하게 잡고 통계 페이지의 **Denied** 열을 보면서 조여 나가세요. 너무 빡빡하면 정상 사용자가 차단됩니다.

---

### 10. 서버 점검(maintenance) 처리

서버를 점검할 때 트래픽만 잠시 빼는 방법입니다. 설정 파일에 `disabled`를 붙이면 그 서버는 처음부터 제외된 채로 뜹니다.

```
backend web_servers
  balance roundrobin
  server web1 10.0.0.11:8080 check
  server web2 10.0.0.12:8080 check disabled
```

다만 실제 운영에서는 **설정 파일을 고치고 리로드하는 것보다 관리 소켓으로 즉시 빼는 편**이 훨씬 빠르고 안전합니다.

```bash
# 점검 시작 — 새 연결을 받지 않음 (기존 연결은 유지)
echo "disable server web_servers/web2" | sudo socat stdio /run/haproxy/haproxy.sock

# 점검 종료 — 다시 투입
echo "enable server web_servers/web2" | sudo socat stdio /run/haproxy/haproxy.sock

# 현재 상태 확인
echo "show servers state" | sudo socat stdio /run/haproxy/haproxy.sock
```

이 방식은 HAProxy를 재시작하지 않으므로 다른 서버의 연결에 전혀 영향을 주지 않습니다. [통계 페이지](#통계stats-페이지)에서 `stats admin`을 켜 두었다면 브라우저 버튼으로도 같은 일을 할 수 있습니다.

---

## 로그 확인하기

이 패키지는 rsyslog 규칙(`/etc/rsyslog.d/49-haproxy.conf`)을 함께 설치해서, 로그를 심각도별로 세 파일에 나눠 저장합니다.

| 파일 | 내용 |
|---|---|
| `/var/log/haproxy/access.log` | 요청 기록 (누가 무엇을 요청했는지) |
| `/var/log/haproxy/status.log` | 상태 변화 (서버가 올라오고 내려간 기록) |
| `/var/log/haproxy/error.log` | 오류 |

```bash
sudo tail -f /var/log/haproxy/access.log
```

로그는 `logrotate` 설정에 따라 **매일 한 번 정리되고 14일치가 압축 보관**됩니다. 따로 관리하지 않아도 디스크가 차지 않습니다.

로그 파일이 계속 비어 있다면 rsyslog가 돌고 있는지 확인하세요. HAProxy는 로그를 직접 파일에 쓰지 않고 rsyslog에 넘기는 구조라, rsyslog가 멈춰 있으면 아무것도 쌓이지 않습니다.

```bash
sudo systemctl status rsyslog
sudo systemctl restart rsyslog
```

systemd 저널에서도 서비스 자체의 기동 로그를 볼 수 있습니다.

```bash
sudo journalctl -u haproxy -f
```

로그가 쌓이면 함께 설치된 `halog` 도구로 분석할 수 있습니다. 응답 시간이 느린 요청을 뽑아내는 등의 통계를 내 줍니다.

```bash
halog -srv < /var/log/haproxy/access.log
```

---

## 새 HAProxy 버전으로 올리기

이 저장소를 관리하면서 가장 자주 하게 될 작업입니다. 생각보다 간단합니다.

**1단계 — 최신 버전 확인.** [haproxy.org](https://www.haproxy.org/) 첫 화면의 "Latest versions" 표에서 원하는 계열의 최신 버전을 확인합니다. 표에 `LTS`라고 적힌 계열이 장기 지원 버전이라 운영 환경에 적합하고, `dev`가 붙은 것은 개발 중인 버전이라 쓰면 안 됩니다.

**2단계 — Makefile 수정.** 저장소의 `Makefile` 맨 위 두 줄만 고치면 됩니다.

```makefile
MAINVERSION?=3.4      # 계열 버전 (앞 두 자리)
VERSION=3.4.3         # 정확한 버전 (세 자리)
```

예를 들어 3.4.5가 나왔다면 `VERSION=3.4.5`로만 바꾸면 되고, 3.6 계열로 옮겨 간다면 `MAINVERSION?=3.6`, `VERSION=3.6.0` 처럼 둘 다 바꿉니다.

**3단계 — 다시 빌드하고 확인.**

```bash
make run-docker
ls -lh RPMS/
```

**4단계 — 검증.** 운영에 올리기 전에 테스트 환경에서 설치해 보고, 버전과 기능이 의도대로 나오는지 확인하세요.

```bash
haproxy -v      # 버전 확인
haproxy -vv     # 켜진 기능 전체 확인
```

> 같은 HAProxy 버전인데 패키지만 다시 만들어 배포해야 한다면(예: 설정 파일 수정), `VERSION` 대신 `RELEASE` 값을 올리세요. `make run-docker RELEASE=2` 처럼 쓰면 `dnf`가 새 패키지로 인식해 업그레이드해 줍니다.

---

## 문제가 생겼을 때

### 서비스가 시작되지 않아요

먼저 무엇이 문제인지 확인합니다. 대부분 설정 파일 문법 오류입니다.

```bash
sudo systemctl status haproxy
sudo journalctl -u haproxy -n 50 --no-pager
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
```

`-c` 검사에서 나오는 메시지는 몇 번째 줄이 잘못됐는지까지 알려 주므로 그대로 따라가면 됩니다.

### 포트가 이미 사용 중이라고 나와요

다른 프로그램이 같은 포트를 쓰고 있는 경우입니다. 누가 쓰는지 확인한 뒤, 그 프로그램을 끄거나 HAProxy 쪽 포트를 바꾸세요.

```bash
sudo ss -tlnp | grep -E ':80|:9000'
```

### 통계 페이지가 안 열려요

순서대로 확인하세요. 서버 안에서는 열리는데 밖에서만 안 된다면 방화벽 문제입니다.

```bash
sudo systemctl is-active haproxy                          # 서비스가 떠 있나
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9000/haproxy_stats   # 200이 나오나
sudo firewall-cmd --list-ports                            # 9000 포트가 열려 있나
```

### SELinux 때문에 막히는 것 같아요

SELinux가 켜진 상태에서는 HAProxy가 비표준 포트에 바인딩하거나 백엔드로 연결하는 것을 막을 수 있습니다. 먼저 SELinux가 원인인지 확인합니다.

```bash
sudo getenforce
sudo ausearch -m avc -ts recent | grep haproxy
```

원인이 맞다면, SELinux를 통째로 끄기보다 **필요한 것만 허용하는 편**이 안전합니다. HAProxy가 임의의 포트로 연결할 수 있게 하려면 아래 한 줄이면 됩니다.

```bash
sudo setsebool -P haproxy_connect_any 1
```

특정 포트를 쓰게 하려면 그 포트를 HTTP 포트로 등록해 줍니다.

```bash
sudo semanage port -a -t http_port_t -p tcp 9000
```

### 설치할 때 의존성 오류가 나요

`rpm -i` 대신 `dnf install`을 쓰세요. `rpm` 명령은 필요한 라이브러리를 자동으로 설치해 주지 않습니다.

```bash
sudo dnf install -y ./haproxy-3.4.3-1.el9.x86_64.rpm
```

### 빌드 도중 다운로드에 실패해요

빌드 과정에서 `haproxy.org`에 접속합니다. 폐쇄망이거나 프록시를 거쳐야 하는 환경이라면 빌드가 여기서 멈춥니다. 사내 프록시가 있다면 Docker 데몬과 컨테이너 양쪽에 프록시 설정이 필요합니다.

---

## 참고 자료

- [HAProxy 공식 홈페이지](https://www.haproxy.org/) — 최신 버전과 지원 기간 확인
- [HAProxy 3.4 설정 매뉴얼](https://docs.haproxy.org/3.4/configuration.html) — 모든 설정 항목의 상세 설명
- [HAProxy 관리 가이드](https://docs.haproxy.org/3.4/management.html) — 운영 중 관리 명령
- [HAProxy 입문 문서](https://docs.haproxy.org/3.4/intro.html) — 개념부터 차근차근

서버에 설치한 뒤에는 매뉴얼이 로컬에도 함께 깔립니다.

```bash
man haproxy
man halog
ls /usr/share/doc/haproxy/
```

---

## 라이선스

HAProxy는 GPLv2+ 라이선스로 배포됩니다. 자세한 내용은 저장소의 `LICENSE` 파일을 참고하세요.
