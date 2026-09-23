"""Verifica en Windows el registro de una sesión RDP real y desasigna la VM."""
from extra_common import *

part = 'windows'
cfg = PARTS[part]
result = {'parte': 4, 'fechaUtc': datetime.now(timezone.utc).isoformat(), 'vm': cfg['vm'], 'grupo': cfg['group'], 'region': cfg['location']}
script = r'''
$ErrorActionPreference = 'Stop'
$start = (Get-Date).AddHours(-4)
$logons = @(Get-WinEvent -FilterHashtable @{LogName='Security';Id=4624;StartTime=$start} -ErrorAction SilentlyContinue | ForEach-Object {
  $x = [xml]$_.ToXml()
  $d = @{}
  foreach ($item in $x.Event.EventData.Data) { $d[$item.Name] = $item.'#text' }
  if ($d.LogonType -eq '10' -and $d.TargetUserName -eq 'azureuser') {
    [ordered]@{fechaUtc=$_.TimeCreated.ToUniversalTime().ToString('o');usuario=$d.TargetUserName;tipo=$d.LogonType;ipOrigen=$d.IpAddress;proceso=$d.LogonProcessName;autenticacion=$d.AuthenticationPackageName}
  }
})
$sessions = @(Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-TerminalServices-LocalSessionManager/Operational';Id=21;StartTime=$start} -ErrorAction SilentlyContinue | ForEach-Object {
  [ordered]@{fechaUtc=$_.TimeCreated.ToUniversalTime().ToString('o');evento=$_.Id;mensaje=$_.Message}
})
[ordered]@{nombre=$env:COMPUTERNAME;rdpConfirmado=($logons.Count -gt 0);logonsTipo10=$logons;eventosSesion=$sessions;sesionesActuales=(query user | Out-String)} | ConvertTo-Json -Depth 7
'''
try:
    response = az(['vm', 'run-command', 'invoke', '-g', cfg['group'], '-n', cfg['vm'], '--command-id', 'RunPowerShellScript', '--scripts', script], timeout=420)
    evidence(part, 'sesion-rdp.json', response)
    message = '\n'.join(v.get('message', '') for v in response.get('value', []))
    match = re.search(r'"rdpConfirmado"\s*:\s*true', message, re.IGNORECASE)
    assert match, 'No se encontró un inicio de sesión RDP de azureuser (evento 4624, tipo 10).'
    result.update({'rdp': 'correcto: sesión remota interactiva, evento 4624 tipo 10', 'estado': 'completado', 'cliente': 'Windows App para macOS'})
    print('Confirmada una sesión RDP real en Windows.', flush=True)
finally:
    stop(part)
    result['estadoFinal'] = 'VM deallocated'
    evidence(part, 'resumen.json', result)
