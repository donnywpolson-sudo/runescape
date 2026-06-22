# Hearthvale Prototype

A small Panda3D vertical slice for a single-player, low-poly, top-down RPG about gathering, crafting, combat, shops, banking, and long-term character progression. It uses placeholder geometry only: tiles, boxes, cylinders, and cones.

## Setup

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

For development or troubleshooting, run the game module directly:

```powershell
python -m game.main
```

To build the Windows launcher:

```powershell
.\launcher\build_launcher.ps1
```

The launcher build requires PyInstaller in the project virtual environment. The
build script does not install it by default; install it explicitly with
`.venv\Scripts\python.exe -m pip install pyinstaller`, or rerun the build script
with `-InstallBuildDependencies` to allow that install step.

Then run the built launcher from the project folder:

```powershell
.\dist\Hearthvale.exe
```

If you move the launcher to the Desktop, it will look for `hearthvale` or
`Hearthvale` next to it. For other locations, set `HEARTHVALE_PROJECT_ROOT` to
this checkout before running it.
`Launch Game.bat`, if present, is only an optional manual fallback for running
`python -m game.main`.

## Test

```powershell
python -m pytest
python -m game.tools.validate_data
```

## Manual Smoke Checklist

After code or data changes that affect gameplay reachability, run `python -m game.main`
and verify:

- Gathering gives items and XP, depletes a node, and later respawns it.
- Bank opens from the bank booth and can deposit and withdraw an item stack.
- Shop opens from a shop object and can sell a selected inventory stack.
- Combat starts from a monster, updates player health, grants combat XP, and drops loot.
- Quest dialogue starts or advances a quest and completion rewards apply once.
- `F5` saves, `F9` loads, and the visible inventory, bank, skills, quest, and combat state persist.
- Built launcher starts the same game entry point when launcher behavior changes.

## Controls

- This checkout shows the local login screen at startup. Set
  `AUTO_LOGIN_USERNAME` in `game/settings.py` to a local username only when you
  want development auto-login.
- Enter a username and password, then select `Register` to create a local account.
- Select `Login` to enter the game with an existing local account.
- Press Tab in the username field to move focus to the password field.
- Press Enter in the password field to attempt login.
- Select `Quit` on the login screen to close the prototype.
- `WASD`: pan camera
- `Q` / `E`: rotate camera
- Mouse wheel: zoom camera
- Hover tiles, objects, and scenery to show their name in the top-center status box.
- Left click ground: move player to a tile
- Left click gameplay objects: perform the default action
- Left click scenery: walk to that tile or adjacent to blocked scenery
- Right click ground, gameplay objects, or scenery: choose an action
- Bottom event log `Up` / `Down`: scroll through previous messages
- In-game `File` menu: save, load, or quit
- In-game `Settings` button: toggle the compact HUD layout.
- There are still no in-game audio/music controls yet.
- `F5`: save the currently logged-in account
- `F9`: load the currently logged-in account
- `Esc`: no quit action; use `File` then `Quit` to close the game while playing
- `I` / `C` / `K`: toggle inventory, clothes/equipment, and skills tabs

## Local Account Data

The login/register screen is local-only. This is not an online MMO account
system yet: there is no server, multiplayer, networking, cloud sync, email
recovery, or real-money/security-sensitive account flow.

Local accounts are stored in `users.db`. Passwords are never stored in
plaintext; each account stores a random per-user salt and a PBKDF2-HMAC
password hash.

Character saves are stored per account in `saves/<username>.json`, after making
the username safe for use as a filename. The `saves/` directory is created
automatically when needed.

## Current MVP Features

- 100x100 scalable tile world with the current starter area, grass, dirt paths, blocked rocks, trees, copper rocks, fishing spots, stumps, depleted rocks, shops, bank, crafting stations, NPCs, and monster spawns.
- Angled top-down camera independent from player movement.
- Left-click movement with grid A* pathfinding.
- Classic-style left/right click interactions for ground, gameplay objects, and scenery, including default actions, walk-to behavior, context menus, and examine options.
- Shared gathering activity system for woodcutting, mining, and fishing with JSON-defined XP, level requirements, item rewards, tiered depletion, respawn state, and required starter tools.
- Data-driven inventory display, bottom-right skills/equipment tabs, bankable coin item stack, fixed-noon world time, compact account HUD without a visible clock, in-game Settings toggle, File menu, and per-account save/load.
- Bank booth with an in-game bank panel for depositing and withdrawing inventory stacks.
- Shop panel for choosing specific sellable inventory stacks instead of instantly selling everything.
- Basic combat skills and equipment requirements for wielding higher-tier weapons and shields.
- Data validation for `items.json`, `skills.json`, `world.json`, `recipes.json`, and `quests.json`.

## Next Recommended Systems

- Add optional imported art assets through the procedural renderer hook.
- Continue expanding character/object animation variety.
- Expand the map data and object definitions.
