#!/bin/sh
# Partes da Harumi que precisam de root. Uso:  sudo sh ~/harumi/root/install-root.sh
# - harumi-cpufreq: baixa a frequencia dos nucleos grandes em degraus quando a placa esquenta (ver harumi_cpufreq.py).
set -eu
D="$(cd "$(dirname "$0")" && pwd)"
install -m 755 "$D/harumi_cpufreq.py" /usr/local/sbin/harumi-cpufreq
cat > /etc/systemd/system/harumi-cpufreq.service <<EOF
[Unit]
Description=Harumi Auto OS - governador termico (teto de frequencia dos nucleos grandes)

[Service]
ExecStart=/usr/bin/python3 /usr/local/sbin/harumi-cpufreq
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now harumi-cpufreq.service
echo "harumi-cpufreq ativo. Estado: cat /run/harumi-cpufreq.json"
