#!/usr/bin/env python3
"""Comprueba archivos históricos locales. No consulta Azure ni usa credenciales."""

import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "evidencias/verificacion-2026-09-23"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_documents():
    paths = sorted((ROOT / "evidencias").rglob("*.json"))
    paths += sorted((ROOT / "plantillas").rglob("*.json"))
    require(bool(paths), "No se encontraron JSON")
    for path in paths:
        read_json(path)
    return f"{len(paths)} JSON legibles"


def template_hashes():
    folder = ROOT / "plantillas"
    provenance = read_json(folder / "procedencia-catalogo.json")
    for name, field in (("original", "sha256Original"), ("adaptada", "sha256Adaptada")):
        require(
            digest(folder / f"catalogo-linux.{name}.json") == provenance[field],
            f"SHA256 distinto en la plantilla {name}",
        )
    return "Original y adaptación coinciden con sus SHA256"


def image_and_snapshot():
    folder = ROOT / "evidencias/capturas"
    provenance = read_json(folder / "procedencia.json")
    capture = folder / provenance["archivo"]
    require(capture.read_bytes().startswith(b"\xff\xd8\xff"), "La captura no es JPEG")
    require(digest(capture) == provenance["sha256"], "SHA256 distinto en la captura")
    manifest = read_json(SNAPSHOT / "integridad.json")["archivos"]
    require(len(manifest) == 8, "Se esperaban ocho registros en el manifiesto")
    for name, expected in manifest.items():
        require(digest(SNAPSHOT / name) == expected, f"SHA256 distinto: {name}")
    return "Captura y ocho registros coinciden con sus manifiestos"


def persistence():
    before = (ROOT / "evidencias/07-montaje-disco.txt").read_text()
    after = (ROOT / "evidencias/08-persistencia-tras-reinicio.txt").read_text()
    previous = re.search(r"Arranque anterior: ([0-9a-f-]{36})", after)
    current = re.search(r"Arranque nuevo: ([0-9a-f-]{36})", after)
    require(previous and current, "Faltan identificadores de arranque")
    require(previous.group(1) != current.group(1), "El identificador de arranque no cambió")
    require("/datos /dev/sdb1 ext4" in before, "Falta el montaje inicial")
    require("/datos /dev/sda1 ext4" in after, "Falta el montaje tras reiniciar")
    require(
        "UUID=ef492f4a-1423-404e-98e1-6cc1392162b1 /datos ext4 defaults,nofail"
        in before,
        "Falta la configuración persistente por UUID",
    )
    for filename in ("prueba-iaas.txt", "prueba-persistencia.bin"):
        for record in (before, after):
            require(f"{filename}: OK" in record, f"Falta integridad de {filename}")
    return "Nuevo arranque, montaje conservado y dos archivos con SHA256 OK"


def linux_and_deployment():
    for part in ("ubuntu", "plantilla"):
        record = (SNAPSHOT / f"{part}-ssh.txt").read_text()
        for token in (f"vm-{part}-iaas", "Ubuntu 22.04.5 LTS", "VALIDACION_SSH_OK"):
            require(token in record.splitlines(), f"Falta {token} en {part}")
    require(
        "LECTURA_ESCRITURA_OK" in (SNAPSHOT / "ubuntu-ssh.txt").read_text(),
        "Falta prueba de lectura y escritura",
    )
    deployments = read_json(SNAPSHOT / "plantilla-despliegues.json")
    require(
        any(d["nombre"] == "despliegue-plantilla" and d["estado"] == "Succeeded"
            for d in deployments),
        "No se encontró el despliegue correcto",
    )
    return "Ambas Ubuntu identificadas, lectura/escritura y despliegue correctos"


def run_command_payload(filename):
    result = read_json(SNAPSHOT / filename)
    outputs = [
        item["message"] for item in result["value"]
        if item["code"] == "ComponentStatus/StdOut/succeeded"
    ]
    require(len(outputs) == 1, f"Salida de Azure inesperada: {filename}")
    return json.loads(outputs[0])


def windows_rdp():
    system = run_command_payload("windows-sistema.json")
    require(system["nombre"] == "vm-win-iaas", "Nombre Windows inesperado")
    require("Windows Server 2022 Datacenter" in system["sistema"], "Sistema inesperado")
    require(system["servicioRDP"] == "Running" and system["puerto3389"], "Servicio RDP no disponible")
    require(system["nla"] == 1 and system["cuentaHabilitada"], "NLA o cuenta no habilitada")
    session = run_command_payload("windows-sesion.json")
    require(session["rdpNuevoConfirmado"] is True, "No se confirmó un nuevo inicio RDP")
    require(any(str(e["tipo"]) == "10" for e in session["iniciosSesion"]), "Falta inicio tipo 10")
    require(
        any("rdp-tcp" in line and "Active" in line for line in session["sesiones"].splitlines()),
        "Falta una sesión RDP activa",
    )
    return "Windows identificado, NLA, nuevo inicio tipo 10 y sesión activa"


def final_state():
    machines = read_json(SNAPSHOT / "estado-final.json")["maquinas"]
    require(
        {vm["nombre"] for vm in machines} ==
        {"vm-ubuntu-iaas", "vm-plantilla-iaas", "vm-win-iaas"} and len(machines) == 3,
        "Inventario de VM inesperado",
    )
    disks = []
    for vm in machines:
        require(vm["estado"] == "VM deallocated", f"VM no desasignada: {vm['nombre']}")
        require(vm["provision"] == "Succeeded", f"Aprovisionamiento: {vm['nombre']}")
        disks.extend(vm["discos"])
    require(len(disks) == 4, "Se esperaban cuatro discos")
    require(
        all(d["gb"] == 32 and d["tipo"] == "Standard_LRS"
            and d["estado"] == "Reserved" and d["provision"] == "Succeeded" for d in disks),
        "Tamaño, tipo o estado de disco inesperado",
    )
    return "Registro final: tres VM desasignadas y cuatro discos de 32 GiB"


def markdown_without_code(path):
    return re.sub(r"^```.*?^```[^\n]*$", "", path.read_text(), flags=re.M | re.S)


def anchors(path):
    found, counts = set(), {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", markdown_without_code(path), re.M):
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        found.add(slug if count == 0 else f"{slug}-{count}")
    return found


def markdown_links():
    failures, count = [], 0
    paths = [ROOT / name for name in ("README.md", "Guia-tecnica.md",
                                     "Plantilla-del-catalogo.md", "Windows-y-RDP.md")]
    paths += sorted((ROOT / "docs").rglob("*.md"))
    paths += sorted((ROOT / "evidencias").rglob("*.md"))
    for path in paths:
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", markdown_without_code(path)):
            url = urlsplit(target.strip("<>"))
            if url.scheme or url.netloc:
                continue
            destination = (path.parent / unquote(url.path)).resolve() if url.path else path
            label = f"{path.relative_to(ROOT)} → {target}"
            count += 1
            if not destination.exists():
                failures.append(label)
            elif url.fragment and destination.suffix == ".md":
                if unquote(url.fragment) not in anchors(destination):
                    failures.append(label)
    require(not failures, "Enlaces o anclas rotos:\n" + "\n".join(failures))
    return f"{count} enlaces locales y anclas válidos"


def main():
    checks = (json_documents, template_hashes, image_and_snapshot, persistence,
              linux_and_deployment, windows_rdp, final_state, markdown_links)
    failures = 0
    print("Verificación local de evidencias históricas · sin conexión a Azure\n")
    for check in checks:
        try:
            print(f"OK · {check()}")
        except (OSError, ValueError, KeyError, TypeError) as error:
            failures += 1
            print(f"ERROR · {check.__name__}: {error}", file=sys.stderr)
    print(f"\nResultado: {len(checks) - failures}/{len(checks)} comprobaciones correctas.")
    print("No acredita el estado actual de las VM ni certifica el origen externo de los archivos.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
