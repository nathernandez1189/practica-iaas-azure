from pathlib import Path
import json
import os
import subprocess

BASE = Path(__file__).resolve().parents[1]
RG = 'rg-practica-iaas'
VM = 'vm-ubuntu-iaas'
LOCATION = 'chilecentral'
SUBSCRIPTION = os.environ.get('AZURE_SUBSCRIPTION_ID', '')
EVIDENCES = BASE / 'resultados-locales' / 'evidencias'
ENV = os.environ.copy()


def az(args, *, timeout=180):
    if not SUBSCRIPTION:
        raise RuntimeError('Configura AZURE_SUBSCRIPTION_ID antes de operar recursos de Azure. Consulta README.md.')
    result = subprocess.run(['az', *args, '--subscription', SUBSCRIPTION, '--only-show-errors', '-o', 'json'],
                            env=ENV, text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return json.loads(result.stdout) if result.stdout.strip() else None


def save(name, value):
    EVIDENCES.mkdir(parents=True, exist_ok=True)
    path = EVIDENCES / name
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    return path
