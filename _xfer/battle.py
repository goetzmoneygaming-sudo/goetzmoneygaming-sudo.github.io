# -*- coding: utf-8 -*-
"""
battle.py -- BONES for Glitchling battles (Nova, 2026-11-02 night
session, on Sam's "bones for ... fighting" instruction).

Battling itself is NOT yet an approved feature -- Sam asked for the
foundation only. Everything tunable lives in the PROPOSED block
below and is flagged as unapproved; the module is deliberately not
hooked to chat and drives no overlay. When Sam approves the shape,
the listener grows !battle / !baccept / !bdecline exactly the way
trades were wired (trigger files -> this module -> a future
battle page + chat announce).

Shape:
  * BattleBook mirrors the ledger trade pattern: a viewer opens a
    challenge naming one of their creatures and a target viewer;
    the target accepts or declines within CHALLENGE_TTL seconds;
    one open challenge per viewer.
  * On accept, the battle AUTO-RESOLVES (chat games run
    themselves; nobody inputs moves): alternating strikes until
    one side hits 0 HP or the strike cap decides it on remaining
    HP fraction.
  * Damage = BASE_DMG x attacker tier factor x type multiplier
    (type chart) x rng variance. HP scales with tier. A shiny
    fighter gets a small HP bonus.
  * Results persist to their own files (battle_state.json for
    open challenges, battle_record.json for win/loss) -- the
    collection ledger is never touched by battles.
  * resolve() returns the full strike log so a future page or
    Cache line can narrate the fight beat by beat.

Run directly to self-test:  python battle.py
"""

import json
import os
import random
import time

# ---------------------------------------------------------------------------
# PROPOSED CONSTANTS -- Sam has NOT approved these numbers. They exist
# so the bones run end-to-end; tuning them is his call.
# ---------------------------------------------------------------------------
CHALLENGE_TTL = 60          # seconds, same as trade offers
BASE_DMG = 7
STRIKE_CAP = 40
VARIANCE = (0.85, 1.15)
STRONG = 1.5
WEAK = 0.67
SHINY_HP_BONUS = 1.05
HP_BY_TIER = {"COMMON": 42, "UNCOMMON": 54, "RARE": 70, "CHASE": 84}
ATK_BY_TIER = {"COMMON": 1.0, "UNCOMMON": 1.12, "RARE": 1.3, "CHASE": 1.45}

# Species -> (type, tier). Mirrors field-notes-v4.md exactly.
SPECIES_INFO = {
    "pingsqueak": ("VOLT", "COMMON"), "curslime": ("PIXEL", "COMMON"),
    "bittybat": ("STATIC", "COMMON"), "cachemunk": ("DATA", "COMMON"),
    "fizzbyte": ("NEON", "COMMON"), "trackpadger": ("CHROME", "COMMON"),
    "bitbloom": ("NEON", "COMMON"), "pondbyte": ("STATIC", "COMMON"),
    "encore": ("ECHO", "COMMON"), "bootsect": ("DATA", "COMMON"),
    "dialtone": ("ECHO", "COMMON"), "glitchpup": ("GLITCH", "UNCOMMON"),
    "mothboard": ("ECHO", "UNCOMMON"), "mainlet": ("VOLT", "UNCOMMON"),
    "perfora": ("DATA", "UNCOMMON"), "cathermit": ("STATIC", "UNCOMMON"),
    "tapeloop": ("ECHO", "UNCOMMON"), "pipedream": ("NEON", "UNCOMMON"),
    "stackquack": ("DATA", "UNCOMMON"), "lowbatt": ("VOLT", "UNCOMMON"),
    "joyrider": ("CHROME", "UNCOMMON"), "mintmark": ("MINT", "RARE"),
    "overstack": ("GLITCH", "RARE"), "motherwyrm": ("DATA", "RARE"),
    "rackshasa": ("CHROME", "RARE"), "testcard": ("NEON", "RARE"),
}
TYPES = ["VOLT", "STATIC", "DATA", "NEON", "CHROME", "PIXEL",
         "GLITCH", "ECHO", "MINT"]

# PROPOSED type chart: a ring. Each type hits the NEXT TWO types in
# the ring hard (STRONG) and is hit hard by the two BEFORE it (so its
# own attacks into those two are WEAK). Everything else is neutral,
# mirror matches neutral. Balanced by construction: every type has
# exactly 2 strong, 2 weak, 5 neutral.
RING = ["VOLT", "CHROME", "DATA", "PIXEL", "GLITCH",
        "NEON", "ECHO", "MINT", "STATIC"]


def type_multiplier(atk_type, def_type):
    if atk_type == def_type:
        return 1.0
    i = RING.index(atk_type)
    j = RING.index(def_type)
    ahead = (j - i) % len(RING)
    if ahead in (1, 2):
        return STRONG
    if ahead in (len(RING) - 2, len(RING) - 1):
        return WEAK
    return 1.0


# ---------------------------------------------------------------------------
# One fighter / one fight
# ---------------------------------------------------------------------------

class Fighter:
    def __init__(self, owner, species, shiny=False):
        if species not in SPECIES_INFO:
            raise ValueError("unknown species: %r" % species)
        self.owner = owner
        self.species = species
        self.type, self.tier = SPECIES_INFO[species]
        hp = HP_BY_TIER[self.tier]
        if shiny:
            hp = round(hp * SHINY_HP_BONUS)
        self.max_hp = hp
        self.hp = hp

    def strike_damage(self, defender, rng):
        mult = type_multiplier(self.type, defender.type)
        raw = BASE_DMG * ATK_BY_TIER[self.tier] * mult
        raw *= rng.uniform(*VARIANCE)
        return max(1, round(raw)), mult


def resolve_battle(a, b, rng=None):
    """Run the whole fight. a/b are Fighters. Returns the result
    record with the full turn log for narration."""
    rng = rng or random
    first, second = (a, b) if rng.random() < 0.5 else (b, a)
    turns = []
    striker, target = first, second
    n = 0
    while a.hp > 0 and b.hp > 0 and n < STRIKE_CAP:
        dmg, mult = striker.strike_damage(target, rng)
        target.hp = max(0, target.hp - dmg)
        n += 1
        turns.append({
            "n": n, "by": striker.owner, "species": striker.species,
            "dmg": dmg, "mult": mult,
            "target": target.species, "target_hp": target.hp,
        })
        striker, target = target, striker
    if a.hp <= 0 and b.hp <= 0:
        winner = None
    elif b.hp <= 0:
        winner = a
    elif a.hp <= 0:
        winner = b
    else:  # strike cap: remaining HP fraction decides
        fa, fb = a.hp / a.max_hp, b.hp / b.max_hp
        winner = a if fa > fb else (b if fb > fa else None)
    loser = b if winner is a else (a if winner is b else None)
    return {
        "winner": winner.owner if winner else None,
        "winner_species": winner.species if winner else None,
        "loser": loser.owner if loser else None,
        "loser_species": loser.species if loser else None,
        "strikes": n,
        "turns": turns,
        "final_hp": {a.species: a.hp, b.species: b.hp},
    }


# ---------------------------------------------------------------------------
# Challenge book (mirrors the ledger's trade-offer lifecycle)
# ---------------------------------------------------------------------------

def _atomic(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    os.replace(tmp, path)


class BattleBook:
    def __init__(self, state_path, record_path):
        self.state_path = state_path
        self.record_path = record_path
        self.state = self._load(state_path, {"challenges": []})
        self.record = self._load(record_path, {})

    @staticmethod
    def _load(path, default):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return default

    def _save(self):
        _atomic(self.state_path, self.state)
        _atomic(self.record_path, self.record)

    def expire(self, now=None):
        now = time.time() if now is None else now
        self.state["challenges"] = [
            c for c in self.state["challenges"] if c["expires"] > now]

    def open_challenge(self, from_user, to_user, species, now=None):
        now = time.time() if now is None else now
        self.expire(now)
        a, b = from_user.strip().lower(), to_user.strip().lower()
        if a == b:
            raise ValueError("cannot battle yourself")
        if species not in SPECIES_INFO:
            raise ValueError("unknown species: %r" % species)
        for c in self.state["challenges"]:
            if a in (c["from"], c["to"]) or b in (c["from"], c["to"]):
                raise ValueError("one of these viewers already has an open challenge")
        ch = {"id": "battle-%d" % int(now * 1000), "from": a, "to": b,
              "species": species, "created": now,
              "expires": now + CHALLENGE_TTL}
        self.state["challenges"].append(ch)
        self._save()
        return dict(ch)

    def _find(self, user):
        user = user.strip().lower()
        for c in self.state["challenges"]:
            if user in (c["from"], c["to"]):
                return c
        return None

    def decline(self, user):
        ch = self._find(user)
        if not ch:
            raise ValueError("no open challenge for %s" % user)
        if ch["to"] != user.strip().lower():
            raise ValueError("only the challenged viewer can decline")
        self.state["challenges"].remove(ch)
        self._save()
        return ch

    def accept(self, user, defender_species, rng=None, shiny=None, now=None):
        """user = the challenged viewer; defender_species = THEIR
        creature. shiny = optional {username: bool} overrides.
        Returns the battle result record."""
        now = time.time() if now is None else now
        self.expire(now)
        ch = self._find(user)
        if not ch:
            raise ValueError("no open challenge for %s" % user)
        if ch["to"] != user.strip().lower():
            raise ValueError("only the challenged viewer can accept")
        shiny = shiny or {}
        fa = Fighter(ch["from"], ch["species"],
                     shiny=shiny.get(ch["from"], False))
        fb = Fighter(ch["to"], defender_species,
                     shiny=shiny.get(ch["to"], False))
        result = resolve_battle(fa, fb, rng=rng)
        result["id"] = ch["id"]
        result["from"] = ch["from"]
        result["to"] = ch["to"]
        self.state["challenges"].remove(ch)
        if result["winner"]:
            w = self.record.setdefault(result["winner"], {"w": 0, "l": 0})
            l = self.record.setdefault(result["loser"], {"w": 0, "l": 0})
            w["w"] += 1
            l["l"] += 1
        self._save()
        return result


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _selftest():
    rng = random.Random(1102)
    checks = []

    # chart: every type has exactly 2 strong, 2 weak; reciprocity holds
    for t in TYPES:
        strong = [d for d in TYPES if type_multiplier(t, d) == STRONG]
        weak = [d for d in TYPES if type_multiplier(t, d) == WEAK]
        checks.append(("%s has 2 strong / 2 weak" % t,
                       len(strong) == 2 and len(weak) == 2))
        for d in TYPES:
            if type_multiplier(t, d) == STRONG:
                checks.append(("reciprocal %s>%s" % (t, d),
                               type_multiplier(d, t) == WEAK))

    # 300 random battles complete with legal outcomes
    ok = True
    species = sorted(SPECIES_INFO)
    for _ in range(300):
        fa = Fighter("a", rng.choice(species), shiny=rng.random() < 0.02)
        fb = Fighter("b", rng.choice(species), shiny=rng.random() < 0.02)
        res = resolve_battle(fa, fb, rng=rng)
        if res["strikes"] < 1 or res["strikes"] > STRIKE_CAP:
            ok = False
        if res["winner"] is not None and res["final_hp"][res["loser_species"]] > res["final_hp"][res["winner_species"]] and res["strikes"] < STRIKE_CAP:
            ok = False
    checks.append(("300 simulated battles resolve legally", ok))

    # state machine: open -> decline; open -> accept -> record written
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        book = BattleBook(os.path.join(td, "s.json"),
                          os.path.join(td, "r.json"))
        book.open_challenge("Alice", "Bob", "glitchpup", now=1000.0)
        try:
            book.open_challenge("Alice", "Carol", "curslime", now=1001.0)
            checks.append(("second open challenge blocked", False))
        except ValueError:
            checks.append(("second open challenge blocked", True))
        book.decline("bob")
        checks.append(("decline clears the challenge",
                       book._find("alice") is None))
        book.open_challenge("Alice", "Bob", "glitchpup", now=2000.0)
        res = book.accept("bob", "curslime", rng=rng, now=2001.0)
        checks.append(("accept resolves a battle",
                       res["strikes"] >= 1 and "turns" in res))
        checks.append(("record written",
                       sum(v["w"] for v in book.record.values()) == 1))
        book.open_challenge("Alice", "Bob", "glitchpup", now=3000.0)
        book.expire(now=3000.0 + CHALLENGE_TTL + 1)
        checks.append(("expiry clears stale challenges",
                       book._find("alice") is None))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(("PASS " if ok else "FAIL ") + name)
    print("battle.py selftest: %d checks, %d passed, %d failed"
          % (len(checks), len(checks) - len(failed), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
