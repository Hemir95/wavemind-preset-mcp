# WaveMind Preset MCP

A [Model Context Protocol](https://modelcontextprotocol.io) server that creates and manages
**presets for WaveMind NAM Universal II** (the free NAM plugin that chains Pedal NAM → Amp NAM
→ 4 Cabinet IR slots → EQ → FX) by writing the plugin's own preset files directly — no GUI
automation, no host DAW tricks.

## How it works

WaveMind NAM Universal II stores user presets as **plain XML**:

```
%APPDATA%\WaveMind\NAM Universal II\Presets\User\<name>.preset
```

The root `<PARAMETERS>` element carries the slot file paths as attributes:

| Attribute | Slot |
|---|---|
| `profileFileAmplifiers` | Amplifier `.nam` capture |
| `profileFilePedals` | Pedal `.nam` capture (optional) |
| `impulseFile0..3` | Cabinet IR `.wav` files (up to 4, optional) |

plus ~177 `<PARAM id="..." value="..."/>` children: amp EQ (bass/mid/treble/presence), gate,
IntellEQ, per-slot level/pan/mic/IR-shift/HPF/LPF, delay, reverb, chorus, compressor...

The **visible preset name = the file name**, and the plugin picks up new/edited/deleted
`.preset` files **live** — no restart needed. So an agent (or a script) can generate complete
presets pointing at an organized capture library, and they appear in the plugin instantly.

## Setup

Install (either way):

```bash
# with uv/uvx (recommended - no install step, cached)
uvx wavemind-preset-mcp

# or classic pip
pip install wavemind-preset-mcp
```

1. **Create the template**: open WaveMind NAM Universal II in any DAW, load anything, and
   **save a preset**. Then copy that `.preset` file to this repo's folder as
   `wavemind_mcp/plantilla.preset` (or point `WAVEMIND_TEMPLATE` at it). The template
   provides the full parameter list. (A placeholder template ships with the package — it
   has the correct parameter ids but points at dummy paths, so a real one from your
   plugin is strongly recommended.)
2. **(Optional) Organize your library**: put your `.nam` captures and `.wav` IRs in folders and
   point `WAVEMIND_NAM_DIR` / `WAVEMIND_IR_DIR` at them (used by the search/inventory tools).

## MCP configuration

```json
{
  "mcpServers": {
    "wavemind": {
      "command": "uvx",
      "args": ["wavemind-preset-mcp"],
      "env": {
        "WAVEMIND_NAM_DIR": "C:\\Music\\NAMs",
        "WAVEMIND_IR_DIR": "C:\\Music\\IRs"
      }
    }
  }
}
```

## Tools

| Tool | What it does |
|---|---|
| `create_preset` | Write a new `.preset`: amp + optional pedal + up to 4 cab IRs + any parameters |
| `list_presets` | List user presets with their amp/pedal/cab slots |
| `read_preset` | Inspect a preset (slots + key parameters) |
| `delete_preset` | Delete a preset |
| `list_param_ids` | The full valid parameter catalog from the template |
| `buscar_biblioteca` | Search the organized capture library by text |
| `categorias_biblioteca` | Inventory the library (categories + counts) |

## Built-in engineering defaults

Every generated preset gets, unless overridden:

- **Solo OFF** on all 4 cabinet slots (a soloed slot mutes the rest of the chain)
- **Stereo balance**: symmetric L/R pairs (2 cabs), centered main + equal sides (3), or wide pair
  + centered fillers (4) — so no earpiece ends up silent
- **Phase/time alignment + 90 Hz HPF** on every populated slot (`AlignComp`, `IRShift`, HPF) —
  blending unaligned IRs causes low-frequency comb filtering (a "wobble"); this kills it

## Tips

- Documented per-song amp settings for popular records exist on sites like
  [ToneMirror](https://www.tonemirror.so) and [TonesMatch](https://tonesmatch.com) — use them as
  the `params` for `create_preset` instead of guessing.
- Remember **input calibration**: each `.nam` capture was taken at a specific input level
  (often stated in its Tone3000 page). If an amp sounds under/over-distorted, calibrate your
  interface's input level first.
- Tone3000 hosts free NAM captures; the download URLs are public and the IDs live in each
  tone page's payload.

## Disclaimer

This is an independent community tool. It is not affiliated with or endorsed by WaveMind, Tone3000, or any plugin vendor. "NAM" refers to the open Neural Amp Modeler
format.
