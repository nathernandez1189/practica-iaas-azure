"""Obtiene pruebas de Windows y prepara el archivo local para RDP."""
from extra_common import *

part = 'windows'
cfg = PARTS[part]
private = private_dir(part)
vm = vm_info(part)
assert vm['powerState'] == 'VM running' and vm['tags']['practica'] == 'iaas'
print('Comprobando Windows Server y el servicio de escritorio remoto...', flush=True)
script = r'''
$ErrorActionPreference = 'Stop'
$os = Get-CimInstance Win32_OperatingSystem
$computer = Get-CimInstance Win32_ComputerSystem
$rdp = Get-CimInstance -Namespace 'root/cimv2/terminalservices' -ClassName Win32_TSGeneralSetting -Filter "TerminalName='RDP-tcp'"
$cert = Get-ChildItem 'Cert:\LocalMachine\Remote Desktop' | Where-Object { $_.Thumbprint -eq $rdp.SSLCertificateSHA1Hash } | Select-Object -First 1
$sha256 = if ($cert) { [BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($cert.RawData)).Replace('-', '') } else { $null }
[ordered]@{
  fechaUtc = (Get-Date).ToUniversalTime().ToString('o')
  nombre = $env:COMPUTERNAME
  sistemaOperativo = $os.Caption
  version = $os.Version
  arquitectura = $os.OSArchitecture
  procesadores = $computer.NumberOfLogicalProcessors
  memoriaGiB = [Math]::Round($computer.TotalPhysicalMemory/1GB,2)
  servicioRDP = (Get-Service TermService).Status.ToString()
  puerto3389 = [bool](Get-NetTCPConnection -LocalPort 3389 -State Listen -ErrorAction SilentlyContinue)
  rdpHabilitado = ((Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server').fDenyTSConnections -eq 0)
  autenticacionNivelRed = $rdp.UserAuthenticationRequired
  certificadoSHA1 = $rdp.SSLCertificateSHA1Hash
  certificadoSHA256 = $sha256
} | ConvertTo-Json -Depth 5
'''
response = az(['vm', 'run-command', 'invoke', '-g', cfg['group'], '-n', cfg['vm'], '--command-id', 'RunPowerShellScript', '--scripts', script], timeout=420)
evidence(part, 'windows-y-servicio-rdp.json', response)
print('Actualizando las IP /32 permitidas para esta conexión...', flush=True)
update_access(part)
ip = str(ipaddress.IPv4Address(vm['publicIps']))
rdp_path = private / 'Windows-IaaS.rdp'
rdp_path.write_text('\n'.join([
    'full address:s:' + ip + ':3389',
    'username:s:' + cfg['vm'] + '\\azureuser',
    'screen mode id:i:1', 'desktopwidth:i:1280', 'desktopheight:i:800',
    'session bpp:i:32', 'authentication level:i:2', 'enablecredsspsupport:i:1',
    'redirectclipboard:i:0', 'drivestoredirect:s:', 'audiomode:i:2',
    'redirectprinters:i:0', 'redirectsmartcards:i:0', 'prompt for credentials:i:1', ''
]))
rdp_path.chmod(0o600)
private_json(private / 'conexion.json', {'ip': ip, 'usuario': cfg['vm'] + '\\azureuser', 'archivoRDP': str(rdp_path)})
print('Archivo RDP preparado. La contraseña permanece en privado/windows/credenciales.json.', flush=True)
