#!/usr/bin/env bash
set -euo pipefail

DISK_LINK=/dev/disk/azure/scsi1/lun0
test -L "$DISK_LINK" || { echo 'No existe el enlace del disco adicional LUN 0.' >&2; exit 1; }
DISK_DEVICE="$(readlink -f "$DISK_LINK")"
test "$(lsblk -dn -o TYPE "$DISK_DEVICE")" = disk
test "$(blockdev --getsize64 "$DISK_DEVICE")" = 34359738368 || { echo 'El disco no tiene los 32 GiB esperados.' >&2; exit 1; }
test "$(lsblk -nr -o TYPE "$DISK_DEVICE" | wc -l)" -eq 1 || { echo 'El disco ya contiene particiones; se detiene el formateo.' >&2; exit 1; }
test -z "$(lsblk -nr -o MOUNTPOINTS "$DISK_DEVICE" | tr -d '[:space:]')"
test -z "$(wipefs --no-act --noheadings --output TYPE "$DISK_DEVICE")" || { echo 'El disco contiene firmas previas; se detiene el formateo.' >&2; exit 1; }
! findmnt --mountpoint /datos >/dev/null 2>&1

printf 'Disco nuevo confirmado: %s; LUN 0; 32 GiB.\n' "$DISK_DEVICE"
parted "$DISK_DEVICE" --script mklabel gpt mkpart primary ext4 1MiB 100%
partprobe "$DISK_DEVICE"
udevadm settle
PARTITION="$(lsblk -nrpo NAME,TYPE "$DISK_DEVICE" | awk '$2 == "part" {print $1}')"
test -n "$PARTITION"
test "$(printf '%s\n' "$PARTITION" | wc -l)" -eq 1
mkfs.ext4 -L DATOS_IAAS "$PARTITION"

FS_UUID="$(blkid -s UUID -o value "$PARTITION")"
test -n "$FS_UUID"
mkdir -p /datos
cp -p /etc/fstab /etc/fstab.antes-practica-iaas
printf 'UUID=%s /datos ext4 defaults,nofail 0 2\n' "$FS_UUID" >> /etc/fstab
findmnt --verify --tab-file /etc/fstab
systemctl daemon-reload
mount /datos
chown azureuser:azureuser /datos
chmod 755 /datos

sudo -u azureuser bash <<'DATA'
set -euo pipefail
printf 'Práctica IaaS: disco administrado adicional de 32 GiB.\nMontaje persistente: /datos.\nCreado el: %s\n' "$(date --iso-8601=seconds)" > /datos/prueba-iaas.txt
dd if=/dev/urandom of=/datos/prueba-persistencia.bin bs=1M count=1 status=none
cd /datos
sha256sum prueba-iaas.txt prueba-persistencia.bin > SHA256SUMS
sha256sum --check SHA256SUMS
DATA

sync
printf '\n--- Montaje verificado ---\n'
findmnt /datos
df -hT /datos
printf '\n--- Discos ---\n'
lsblk -o NAME,HCTL,SIZE,FSTYPE,MOUNTPOINTS
printf '\n--- Configuración persistente ---\n'
tail -n 1 /etc/fstab
printf '\n--- Archivos de prueba ---\n'
ls -lh /datos
