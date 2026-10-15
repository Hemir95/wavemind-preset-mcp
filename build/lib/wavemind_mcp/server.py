"""WaveMind Preset MCP — create and manage presets for WaveMind NAM Universal II.

WaveMind NAM Universal II stores user presets as plain XML files:
    %APPDATA%\\WaveMind\\NAM Universal II\\Presets\\User\\<name>.preset

The preset root element <PARAMETERS> carries the slot file paths as attributes
(profileFileAmplifiers, profileFilePedals, impulseFile0-3) plus ~177 <PARAM
id="..." value="..."/> children for every knob (amp EQ, gate, IntellEQ, the 4
cabinet slots with level/pan/mic/IR-shift/HPF/LPF, delay, reverb, chorus...).

The visible preset name in the plugin equals the file name. The plugin picks
up new .preset files live (no restart needed).
"""

import os
import glob
import xml.etree.ElementTree as XT  # writing only (we generate the files ourselves)
from typing import Optional

import defusedxml.ElementTree as ET  # safe parsing for third-party .preset files

from fastmcp import FastMCP

APPDATA = os.environ.get("APPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Roaming"))
DIR_PRESETS = os.path.join(APPDATA, "WaveMind", "NAM Universal II", "Presets", "User")
PLANTILLA = os.environ.get("WAVEMIND_TEMPLATE", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "plantilla.preset"))
DIR_BIBLIO_NAM = os.environ.get("WAVEMIND_NAM_DIR", os.path.join(os.path.expanduser("~"), "Music", "NAMs"))
DIR_BIBLIO_IR = os.environ.get("WAVEMIND_IR_DIR", os.path.join(os.path.expanduser("~"), "Music", "IRs"))

mcp = FastMCP(
    "wavemind",
    instructions=(
        "Create and manage WaveMind NAM Universal II presets by writing .preset XML "
        "files directly into the plugin's user Presets folder (picked up live). "
        "Point WAVEMIND_NAM_DIR / WAVEMIND_IR_DIR at your organized capture library."
    ),
)


def _ruta_preset(nombre: str) -> str:
    nombre = nombre.strip()
    if not nombre.lower().endswith(".preset"):
        nombre += ".preset"
    return os.path.join(DIR_PRESETS, nombre)


def _root_of(ruta: str):
    root = ET.parse(ruta).getroot()
    return root if root.tag == "PARAMETERS" else root.find("PARAMETERS")


@mcp.tool
def list_presets() -> str:
    """List user presets with their amp/pedal/cab slots."""
    if not os.path.isdir(DIR_PRESETS):
        return "Presets folder not found: " + DIR_PRESETS
    ps = sorted(glob.glob(os.path.join(DIR_PRESETS, "*.preset")))
    if not ps:
        return "(no presets yet - save one from the plugin to create the first)"
    lineas = []
    for p in ps:
        try:
            par = _root_of(p)
            amp = os.path.basename(par.get("profileFileAmplifiers", "") or "")
            pedal = os.path.basename(par.get("profileFilePedals", "") or "")
            cabs = sum(1 for i in range(4) if par.get(f"impulseFile{i}", ""))
            lineas.append(os.path.basename(p)[:-7] + " | amp: " + (amp or "-")
                          + " | pedal: " + (pedal or "-") + " | cabs: " + str(cabs))
        except Exception as e:
            lineas.append(os.path.basename(p) + " | error: " + str(e)[:60])
    return "\n".join(lineas)


@mcp.tool
def read_preset(nombre: str) -> str:
    """Read a preset: slot file paths and key parameters."""
    ruta = _ruta_preset(nombre)
    if not os.path.exists(ruta):
        return "Not found: " + ruta
    par = _root_of(ruta)
    root = ET.parse(ruta).getroot()
    lineas = ["== " + os.path.basename(ruta) + " =="]
    for k in ("profileFileAmplifiers", "profileFilePedals",
              "impulseFile0", "impulseFile1", "impulseFile2", "impulseFile3"):
        v = par.get(k, "")
        lineas.append(k + ": " + (v or "(empty)"))
    params = {p.get("id"): p.get("value") for p in root.findall("PARAM")}
    lineas.append("-- key parameters --")
    for k in ("amplifier_bass", "amplifier_middle", "amplifier_treble", "amplifier_presence",
              "preGain", "postGain", "gate_active", "gateThreshold", "intelleq_active",
              "intelleq_bite", "intelleq_scoopI", "intelleq_air", "slot1Level", "slot1Pan"):
        if k in params:
            lineas.append(k + " = " + str(params[k]))
    return "\n".join(lineas)


@mcp.tool
def create_preset(
    nombre: str,
    ampli_nam: str,
    pedal_nam: Optional[str] = None,
    cab1: Optional[str] = None,
    cab2: Optional[str] = None,
    cab3: Optional[str] = None,
    cab4: Optional[str] = None,
    params: Optional[dict] = None,
) -> str:
    """Create a WaveMind preset (.preset XML written to the User presets folder;
    the plugin lists it live, no restart).

    nombre: visible preset name (becomes the file name).
    ampli_nam: absolute path to the amplifier .nam capture (AMPLIFIER slot).
    pedal_nam: absolute path to a pedal .nam capture (PEDALS slot), optional.
    cab1..cab4: absolute paths to cabinet IR .wav files, optional.
    params: dict of plugin parameter ids to set (run list_param_ids for the full
    catalog), e.g. {"gate_active": "1.0", "gateThreshold": "-52.0",
    "amplifier_bass": "5.5", "intelleq_bite": "2.5"}.
    """
    if not os.path.isfile(PLANTILLA):
        return ("Template not found: " + PLANTILLA +
                " - save any preset from the plugin, then set WAVEMIND_TEMPLATE to its path")
    if not os.path.isfile(ampli_nam):
        return "Amp .nam does not exist: " + ampli_nam
    ruta = _ruta_preset(nombre)
    if os.path.exists(ruta):
        return "A preset with that name already exists: " + os.path.basename(ruta)
    root = ET.parse(PLANTILLA).getroot()
    par = root if root.tag == "PARAMETERS" else root.find("PARAMETERS")
    par.set("presetName", nombre)
    par.set("profileFileAmplifiers", os.path.abspath(ampli_nam))
    par.set("profileBaseFolderAmplifiers", os.path.dirname(os.path.abspath(ampli_nam)))
    if pedal_nam:
        if not os.path.isfile(pedal_nam):
            return "Pedal .nam does not exist: " + pedal_nam
        par.set("profileFilePedals", os.path.abspath(pedal_nam))
        par.set("profileBaseFolderPedals", os.path.dirname(os.path.abspath(pedal_nam)))
    else:
        par.set("profileFilePedals", "")
    cabs = [c for c in (cab1, cab2, cab3, cab4) if c]
    for i in range(4):
        if i < len(cabs):
            if not os.path.isfile(cabs[i]):
                return "Cab IR does not exist: " + cabs[i]
            cabs_abs = os.path.abspath(cabs[i])
            par.set(f"impulseFile{i}", cabs_abs)
            par.set(f"impulseBaseFolder{i}", os.path.dirname(cabs_abs))
            par.set(f"slot{i+1}cabinetPath", "")
            par.set(f"slot{i+1}cabinetID", "-1")
        else:
            par.set(f"impulseFile{i}", "")
    # Automatic stereo balance: symmetric L/R pairs (or centered main + equal sides)
    if len(cabs) == 2:
        par.set("slot1Pan", "-30.0"); par.set("slot2Pan", "30.0")
        par.set("slot1Level", "85.0"); par.set("slot2Level", "85.0")
    elif len(cabs) == 3:
        par.set("slot1Pan", "0.0"); par.set("slot2Pan", "-30.0"); par.set("slot3Pan", "30.0")
        par.set("slot1Level", "100.0"); par.set("slot2Level", "50.0"); par.set("slot3Level", "50.0")
    elif len(cabs) == 4:
        par.set("slot1Pan", "-35.0"); par.set("slot2Pan", "35.0")
        par.set("slot3Pan", "0.0"); par.set("slot4Pan", "0.0")
        par.set("slot1Level", "80.0"); par.set("slot2Level", "80.0")
        par.set("slot3Level", "45.0"); par.set("slot4Level", "45.0")
    ids_validos = {p.get("id") for p in root.findall("PARAM")}
    aplicados, rechazados = [], []
    # Solo OFF by default on all 4 slots (a soloed slot mutes the rest of the chain)
    for i in range(1, 5):
        sid = f"slot{i}Solo"
        if sid in ids_validos and sid not in (params or {}):
            for p in root.findall("PARAM"):
                if p.get("id") == sid:
                    p.set("value", "0.0")
                    break
    # Phase/time alignment + 90 Hz HPF on every populated slot (prevents low-end
    # comb-filtering/wobble when blending multiple IRs)
    for i in range(1, 5):
        if i <= len(cabs):
            for pid, v in ((f"slot{i}AlignCompActive", "1.0"), (f"slot{i}IRShiftActive", "1.0"),
                           (f"slot{i}HPFActive", "1.0"), (f"slot{i}HPF", "90.0")):
                for p in root.findall("PARAM"):
                    if p.get("id") == pid:
                        p.set("value", v)
                        break
    for k, v in (params or {}).items():
        if k in ids_validos:
            for p in root.findall("PARAM"):
                if p.get("id") == k:
                    p.set("value", str(v))
                    aplicados.append(k)
                    break
        else:
            rechazados.append(k)
    tree = XT.ElementTree(root)
    XT.indent(tree, space="  ")
    tree.write(ruta, encoding="UTF-8", xml_declaration=True)
    salida = "Created: " + ruta + " | params applied: " + (",".join(aplicados) or "(none)")
    if rechazados:
        salida += " | rejected ids: " + ",".join(rechazados)
    return salida


@mcp.tool
def delete_preset(nombre: str) -> str:
    """Delete a user preset."""
    ruta = _ruta_preset(nombre)
    if not os.path.exists(ruta):
        return "Not found: " + nombre
    os.remove(ruta)
    return "Deleted: " + os.path.basename(ruta)


@mcp.tool
def list_param_ids() -> str:
    """List every valid parameter id from the template (usable in create_preset params)."""
    if not os.path.isfile(PLANTILLA):
        return "Template not found: " + PLANTILLA
    root = ET.parse(PLANTILLA).getroot()
    return ", ".join(sorted({p.get("id") for p in root.findall("PARAM") if p.get("id")}))


@mcp.tool
def buscar_biblioteca(texto: str, tipo: str = "all") -> str:
    """Search the organized capture library. tipo: 'nam', 'ir' or 'all'."""
    texto = texto.lower().replace(" ", "-")
    raices = []
    if tipo in ("nam", "all"):
        raices.append((DIR_BIBLIO_NAM, "NAM"))
    if tipo in ("ir", "all"):
        raices.append((DIR_BIBLIO_IR, "IR"))
    out = []
    for raiz, etiqueta in raices:
        for r, _, fs in os.walk(raiz):
            for f in fs:
                fl = f.lower()
                if texto in fl and (fl.endswith(".nam") or fl.endswith(".wav")):
                    out.append(etiqueta + " | " + os.path.join(r, f))
    if not out:
        return "(no results)"
    return "\n".join(out[:40]) + ("\n(...and " + str(len(out) - 40) + " more)" if len(out) > 40 else "")


@mcp.tool
def categorias_biblioteca() -> str:
    """Inventory the organized library: NAM categories and IR collections with counts."""
    lineas = ["== NAMs =="]
    for cat in sorted(os.listdir(DIR_BIBLIO_NAM)):
        d = os.path.join(DIR_BIBLIO_NAM, cat)
        if os.path.isdir(d):
            lineas.append(cat + ": " + str(len(os.listdir(d))))
    lineas.append("== IRs ==")
    for cat in sorted(os.listdir(DIR_BIBLIO_IR)):
        d = os.path.join(DIR_BIBLIO_IR, cat)
        if os.path.isdir(d):
            n = sum(len(fs) for _, _, fs in os.walk(d))
            lineas.append(cat + ": " + str(n))
    return "\n".join(lineas)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
