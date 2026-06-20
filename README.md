# RuneScape Valley Prototype

A small Panda3D vertical slice for a single-player, low-poly, top-down RPG inspired by RuneScape and Stardew Valley. It uses placeholder geometry only: tiles, boxes, cylinders, and cones.

## Setup

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

```powershell
python -m game.main
```

## Test

```powershell
python -m pytest
python -m game.tools.validate_data
```

## Controls

- Start at the local login screen.
- Enter a username and password, then select `Register` to create a local account.
- Select `Login` to enter the game with an existing local account.
- Press Enter in the password field to attempt login.
- Select `Quit` on the login screen to close the prototype.
- `WASD`: pan camera
- `Q` / `E`: rotate camera
- Mouse wheel: zoom camera
- Left click ground: move player to a tile
- Right click resource/shop: interact
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

- 30x30 tile world with grass, dirt paths, blocked rocks, trees, copper rocks, fishing spots, stumps, depleted rocks, and one shop/NPC marker.
- Angled RuneScape-style camera independent from player movement.
- Left-click movement with grid A* pathfinding and no-path feedback.
- Right-click interactions that walk adjacent before gathering or selling.
- Shared gathering system for Woodcutting, Mining, and Fishing with JSON-defined XP, level requirements, item rewards, depletion, and respawn state.
- Inventory with logs, copper ore, raw fish, coin balance, simple day/time clock, HUD text, and per-account save/load.
- Data validation for `items.json`, `skills.json`, and `world.json`.

## Next Recommended Systems

- Replace placeholder geometry with art assets.
- Add basic character/object animations.
- Require tools for gathering actions.
- Add a shop panel instead of instant selling.
- Expand the map data and object definitions.
