# Environment Specification

## System & Tooling
- **OS**: Ubuntu Linux (x86_64)
- **Git**: 2.53.0
- **Python**: 3.14.4
- **Node.js**: Chưa cài đặt trực tiếp trên host (dùng container runtime ở các tuần sau)

## Container Runtime
- **Engine**: Podman 5.7.0 (giả lập Docker CLI)
- **Socket Path**: `/run/user/1000/podman/podman.sock`
- **Environment Variable**: `DOCKER_HOST="unix:///run/user/$UID/podman/podman.sock"`
- **Verification**: `docker info` truy vấn thành công cgroup v2 và systemd manager
- **Memory**: 8GB allocated for VM
