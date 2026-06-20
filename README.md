# Hearthvale Prototype

A small Panda3D vertical slice for a single-player, low-poly, top-down RPG about gathering, crafting, combat, shops, banking, and long-term character progression. It uses placeholder geometry only: tiles, boxes, cylinders, and cones.

## Setup

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

Use the built Windows launcher when available:

```powershell
.\dist\Hearthvale.exe
```

The launcher is also copied to the Desktop by `launcher\build_launcher.ps1`:

```powershell
& "$env:USERPROFILE\Desktop\Hearthvale.exe"
```

For development or troubleshooting, run the game module directly:

```powershell
python -m game.main
```

`Launch Game.bat`, if present, is only an optional manual fallback for running
`python -m game.main`. The EXE launcher does not depend on that batch file.

## Test

```powershell
python -m pytest
python -m game.tools.validate_data
```

## Controls

- Start at the local login screen.
- Enter a username and password, then select `Register` to create a local account.
- Select `Login` to enter the game with an existing local account.
- Press Tab in the username field to move focus to the password field.
- Press Enter in the password field to attempt login.
- Select `Quit` on the login screen to close the prototype.
- `WASD`: pan camera
- `Q` / `E`: rotate camera
- Mouse wheel: zoom camera
- Hover tiles and objects to show their name in the top-center status box.
- Left click ground: move player to a tile
- Left click ground item: walk to it and pick it up
- Right click resource/shop/bank/cooking range/training dummy/ground item: choose an action
- Bottom event log `Up` / `Down`: scroll through previous messages
- In-game `File` menu: save, load, or quit
- `F5`: save the currently logged-in account
- `F9`: load the currently logged-in account
- `Esc`: quit

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

- 100x100 scalable tile world with the current starter area, grass, dirt paths, blocked rocks, trees, copper rocks, fishing spots, stumps, depleted rocks, shop, bank, cooking range, and training dummy markers.
- Angled top-down camera independent from player movement.
- Left-click movement with grid A* pathfinding.
- Right-click interactions that walk adjacent before gathering, opening bank/shop panels, or training combat.
- Shared gathering system for woodcutting, mining, and fishing with JSON-defined XP, level requirements, item rewards, depletion, respawn state, and required starter tools.
- Data-driven inventory display, bottom-right skills/equipment tabs, bankable coin item stack, simple day/time clock, compact account/time HUD, File menu, and per-account save/load.
- Bank booth with an in-game bank panel for depositing and withdrawing inventory stacks.
- Shop panel for choosing specific sellable inventory stacks instead of instantly selling everything.
- Basic combat skills and equipment requirements for wielding higher-tier weapons and shields.
- Data validation for `items.json`, `skills.json`, `world.json`, `recipes.json`, and `quests.json`.

## Next Recommended Systems

- Replace placeholder geometry with art assets.
- Add basic character/object animations.
- Expand the map data and object definitions.
