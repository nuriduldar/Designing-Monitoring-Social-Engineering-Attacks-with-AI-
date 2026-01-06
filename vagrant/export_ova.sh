#!/bin/bash

# Export Vagrant VM to OVA file
# Usage: ./export_ova.sh

set -e

VM_NAME="social-engineering-ai-vm"
OVA_FILE="social-engineering-ai-vm.ova"

echo "Exporting Vagrant VM to OVA..."

# Halt the VM if it's running
echo "Halting VM if running..."
vagrant halt || true

# Find the VM UUID
VM_UUID=$(VBoxManage list vms | grep "$VM_NAME" | awk '{print $2}' | sed 's/[{}]//g')

if [ -z "$VM_UUID" ]; then
    echo "ERROR: VM '$VM_NAME' not found."
    echo "Available VMs:"
    VBoxManage list vms
    exit 1
fi

echo "Found VM: $VM_NAME (UUID: $VM_UUID)"

# Export to OVA
echo "Exporting to $OVA_FILE..."
VBoxManage export "$VM_UUID" --output "$OVA_FILE" --ovf20

if [ $? -eq 0 ]; then
    echo "Successfully exported to: $OVA_FILE"
    ls -lh "$OVA_FILE"
else
    echo "ERROR: Export failed"
    exit 1
fi

