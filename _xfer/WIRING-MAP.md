# WIRING MAP — how the stream machine fits together

_Written by Nova after the Nov 2–3, 2026 night wiring session (Sam asleep,
blanket authorization + backup protocol). This is the single inventory of
what talks to what. Update it whenever a piece moves._

## Backups (Sam's protocol)

- `C:\Cache\backups\nova-2026-11-02-presession\` — FROZEN pre-session copy
  (Cache code/config + Streamer.bot JSONs + OBS scenes + basic.ini).
- `C:\Cache\backups\nova-2026-11-02-latest\` — rolling latest-good copy,
  refreshed after every verified success that night.
- Streamer.bot surgical backups also live beside the data:
  `data\actions.json.bak-wiring-1102`, `data\commands.json.bak-wiring-1102`.
- OBS bridge auto-snapshots before every mutating command, plus an explicit
  `backup_now` before the night's OBS work.

## The overlay bus

- `python -m http.server 8000` serves `C:\Cache\` — every overlay page and
  every `*_state.json` is fetched from `http://127.0.0.1:8000/`.
  Verified threading-capable (6 parallel 3.7 MB fetches overlap fine).
- KNOWN QUIRK: when many browser sources load at once, an OBS page can
  starve its static images (they never retry). Cure: bump that source's
  URL `?v=` by one to force a clean reload (done for Claw/Vault: `?v=2`).
  JS-assigned images (fired later, on state changes) are unaffected.
- Rule: ONE writer per state file. The wiring senders are the only
  writers of the game states. `vault_roll.py` was never installed on
  the PC and is retired — `senders.fire_vault` owns `vault_state.json`.

## Game pages (Sun — Gaming collection, scene "Gameplay")

| OBS input | Page | Size / place | State file | Trigger today |
|---|---|---|---|---|
| Game Card Pull | card-pull.html?v=1 | 676×1080 @ (622,0) | card_pull_state.json | engine only — bits trigger waits on Sam's pack price |
| Game Catch | catch-overlay.html?v=1 | 760×760 @ (580,160) | catch_state.json | **LIVE: `!save`** |
| Game Trade | trade-screen.html?v=1 | 676×400 @ (24,24) | trade_state.json | **LIVE: `!trade`/`!accept`/`!decline`** |
| Game Claw | claw-grab.html?v=2 | 900×1440 @ (622,0) ×0.75 | claw_state.json | engine only — waits on Sam's dashboard reward |
| Game Vault | vault-pull.html?v=2 | 800×880 @ (560,100) | vault_state.json | engine only — `!pull` cutover staged, knife still owns it |
| Mental State Bar | mental-state-bar.html?v=1 | 1548×150 @ (186, parked −162) | polls :8765/level | **LIVE: rage_bar_watcher cues** |

All five game pages were frame-verified in OBS on Nov 2–3 (pull, catch,
trade, claw incl. full machine, vault incl. door + gold-bar video).
State files were cleared after testing, so nothing replays at OBS start;
senders recreate them on the next real fire. Pages that see a state file
on load replay it once — that's why the clear matters.

## The wiring engine (C:\Cache\wiring\)

- `ledger.py` — collections of record. State: `wiring\ledger.json`
  (viewers' cards + creatures + open trade offers, 60 s TTL).
  Card art gate: a card is rollable only while `C:\Cache\cards\card-<id>.png`
  exists (Rackshasa stays out until its art lands). The page art folder
  `C:\Cache\assets\cards\` holds the same Series 1 art under bare names.
- `senders.py` — the only state-file writers: fire_card_pull, attempt_catch
  / fire_catch, fire_trade, fire_vault, fire_claw. Catch odds are the
  engine defaults (Common 55 / Uncommon 40 / Rare 25) — Sam has NOT set
  these; the design doc's different table is still an open inconsistency.
- `cooldown.py` — global takeover gate (60 s, Sam-unconfirmed number).
  Not yet in the live path for catch/trade (they're outside takeover
  class); it gates the future bits/reward pieces.
- `battle.py` — BONES ONLY, not hooked to chat. Challenge/accept/decline
  state machine mirroring trades, auto-resolved fights, proposed type
  ring (2 strong / 2 weak per type), records in its own files.
  Self-test: `python battle.py` → 33 checks.
- `pickem.py` — Thursday Pick'em engine (24/24 self-test from Nov 2).
  Still needs: Sam's "Pick'em Entry" dashboard reward + payout call.
- `wiring_listener.py` — CacheStack proc. Consumes trigger files in
  `wiring\triggers\` written by Streamer.bot command actions:
  `catch.txt` (%user%), `trade.txt` (%user%|%rawInput%),
  `accept.txt`, `decline.txt`. Announces through `wiring\announce.txt`
  + poked action **Wiring Announce** (C# read → Send Message as bot).
  Log: `wiring\wiring_listener.log`. Per-viewer `!save` cooldown 45 s.
  Item names in `!trade` resolve card-vs-creature by ownership
  (creature wins only when it's the kind actually owned; both → card).
- `fire_one.py` — Nova's manual test-fire harness (rolls use a
  throwaway ledger state; the live collection is never polluted).
- `selftest.py` — engine self-test (49 checks, run at install).

## Streamer.bot additions (Nov 2–3)

Commands (all grantType everyone): `!save` (30 s user cooldown),
`!trade`, `!accept`, `!decline`. Actions (group Cache, no queue):
Wiring - Save Catch / Trade Offer / Trade Accept / Trade Decline
(write the trigger files) + Wiring Announce. Counts now: 100 actions,
72 commands. Backups: `*.bak-wiring-1102` in the data folder.

## Rage / mental-state

- `rage_meter.py` (stack proc) still serves the level at :8765 — it's
  the single source of truth for the number.
- NEW: `mental-state-bar.html` replaced the old rail. `Rage Meter Big`
  item + input are REMOVED from Gameplay.
- `rage_bar_watcher.py` (stack proc) slides the bar down from the top
  only on a cue: zone change (CHILL <20, SIMMERING <40, HEATING <60,
  RAGING <80, CODE RED ≥80 — the page's own breaks) or a ≥20-point
  jump; 6 s hold, fresh cues extend. Cue numbers are Nova-proposed,
  awaiting Sam's review. Test: touch `C:\Cache\rage_bar_test.flag`.
- The bar overlaps the top-right corner logo art slightly when shown —
  flagged for Sam's eye.

## Cache slide (v3, installed Nov 2 before this session)

- `cache_slide_listener.py` (stack proc) drives Cache Front directly
  over the OBS websocket (the bridge queue's ~3 s polling was the old
  sync bug). START_DELAY_S 0.45, glide 0.70 s, spoken lines only.

## Goetz Quest (verified healthy Nov 3, untouched)

- `boss_battle.py` + `game_cycler.py` running (rotation: goetzquest
  600 s / bingo 600 s, war disabled).
- SB group GoetzQuest: GQ Buy-In (reward, 500 GM) → boss_buyin_queue.txt;
  GQ Attack (`!attack`) → boss_attack_queue.txt; GQ Special (reward,
  1000 GM) → boss_special_queue.txt; GQ Reset → boss_reset.flag.
- OBS 'Goetz Quest' input = local file
  `C:/Cache/Game Assets/Dungeon Crawl/goetz_quest_assets/goetz_quest_overlay.html`.

## Session scratch

Nova's one-night staging (probe scripts, frames, staged SB copies) is
archived, not deleted: `C:\Cache\nova-session-1102\`.
The `_xfer/` folder in the GitHub Pages repo was the night's file
shuttle (raw CDN) — contents are stream art + the files listed here.
