#!/bin/bash

pkill -f ifplugd
pkill -f "console-kit"
service udev stop
pkill -f "net.agent"
service ssh stop
service ntp stop
service network-manager stop
service dbus stop
pkill -f "policy"
pkill -f "crclient"
pkill -f "dhclient"

echo "performance" > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
