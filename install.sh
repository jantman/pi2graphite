#!/bin/bash

echo "Installing packages..."
for pkname in haveged python-virtualenv python-pip; do
    if dpkg -l | grep -q $pkname; then
        echo "$pkname already installed"
        continue
    fi
    echo "Installing: $pkname"
    apt-get -y install $pkname
done

if [[ -e bin/python ]]; then
    echo "Virtualenv already exists"
else
    echo "Creating virtualenv..."
    virtualenv .
fi

echo "Running bin/python setup.py develop"
bin/python setup.py develop

PYTHON=$(readlink -f bin/python)
echo "Found python binary as: $PYTHON"
BINPATH=$(readlink -f bin/pi2graphite)
echo "Found pi2graphite binary as: $BINPATH"

# add templated systemd unit
if [[ -e /etc/systemd/system/pi2graphite.service ]]; then
    echo "Systemd unit already exists at: /etc/systemd/system/pi2graphite.service"
else
    echo "Templating systemd unit file at: /etc/systemd/system/pi2graphite.service"
    cat <<EOF >/etc/systemd/system/pi2graphite.service
[Unit]
Description=pi2graphite service

[Service]
Type=simple
ExecStart=$PYTHON $BINPATH
RestartSec=10
Restart=always
EOF
    echo "Executing systemctl daemon-reload"
    systemctl daemon-reload
fi

# enable service
if systemctl list-unit-files | grep pi2graphite | grep -q enabled; then
    echo "systemd service already enabled"
else
    echo "enabling systemd service"
    systemctl enable pi2graphite.service
fi

if [[ -e /etc/pi2graphite.json ]]; then
    echo "Config file already exists at: /etc/pi2graphite.json"
    echo "Ensure it's correct, then 'systemctl start pi2graphite' or reboot"
    exit 0
fi

echo "Generating example config to /etc/pi2graphite.json"
bin/pi2graphite --example-config > /etc/pi2graphite.json
echo "DONE."
echo "Edit the config file at /etc/pi2graphite.json, then 'systemctl start pi2graphite' or reboot"

