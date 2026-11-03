# -*- coding: utf-8 -*-
"""
meme_keeper.py -- the meme queue keeper (Nova, 2026-11-03, v2).

Sam's rule: memes never overlap. The Fifine deck buttons fire OBS
Show + a timed Hide directly (one-shots); two presses close together
would overlap, and the deck has no cross-button queue. This keeper
is that queue, enforced on the OBS side:

  * Watches the 11 meme items in the Memes scene (direct
    obs-websocket, ~0.15 s poll).
  * The first meme to appear becomes the ACTIVE play and runs its
    full duration (the same table the deck one-shots use).
  * Any other meme appearing while one is active is hidden at once
    and QUEUED (FIFO). When the active play's time is up, the
    keeper hides it and starts the next in line fresh.
  * A deck button's stale Hide can land mid-play on a queued meme
    (it was scheduled from the press, not the play). If the ACTIVE
    meme is ever found hidden before its time is up, the keeper
    re-shows it once -- the stale timer fires only once.
  * At boot, a meme found on is adopted as active with a fresh
    window (post-restart autoplay cleanup).

v2 note: v1 looped forever -- it acted on a state snapshot taken
before its own change, "re-discovered" the meme it had just ended,
and its stale-hide guard then resurrected it. v2 consumes the whole
tick on any transition it causes and re-reads state fresh.

Fail-silent toward the stream, fail-loud toward meme_keeper.log.
Registered as a CacheStack proc.
"""
import os
import sys
import time

CD = r"C:\Cache"
LOG = os.path.join(CD, "meme_keeper.log")
SCENE = "Memes"
POLL_S = 0.15
TAIL_S = 0.2

DURATIONS = {
    "Another One": 11.03, "DMG": 3.27, "Dog Shit": 6.10,
    "Here We Go": 3.20, "KO": 3.83, "OMG": 5.87, "Shaq": 3.40,
    "TWSS": 1.83, "What?": 2.27, "Who are you?": 6.97, "Wow!": 4.27,
}


def log(m):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%H:%M:%S ") + m + "\n")
    except OSError:
        pass


class Obs:
    def __init__(self):
        self.session = None
        self.ids = {}

    def ensure(self):
        if self.session is not None:
            return True
        try:
            sys.path.insert(0, CD)
            import obs_bridge
            password = os.environ.get("OBS_WS_PASSWORD", "")
            port = int(os.environ.get("OBS_WS_PORT", "4455"))
            if not password:
                log("err no OBS_WS_PASSWORD")
                return False
            self.session = obs_bridge.obs_connect(port, password)
            self.ids = {}
            for name in DURATIONS:
                try:
                    self.ids[name] = obs_bridge.resolve_item_id(
                        self.session, SCENE, {"sceneItemName": name})
                except Exception:
                    pass
            log("ws connected, %d meme items resolved" % len(self.ids))
            return bool(self.ids)
        except Exception as e:
            self.session = None
            log("err connect %r" % (e,))
            return False

    def states(self):
        resp = self.session.request("GetSceneItemList", {"sceneName": SCENE})
        return {it.get("sourceName"): bool(it.get("sceneItemEnabled"))
                for it in resp.get("sceneItems", [])
                if it.get("sourceName") in DURATIONS}

    def set_enabled(self, name, on):
        try:
            self.session.request("SetSceneItemEnabled", {
                "sceneName": SCENE,
                "sceneItemId": self.ids[name],
                "sceneItemEnabled": bool(on),
            })
            return True
        except Exception as e:
            log("err set %s %r" % (name, e))
            self.session = None
            return False


def main():
    obs = Obs()
    log("start v2: meme queue keeper watching")
    active = None
    active_until = 0.0
    queue = []
    booted = False
    while True:
        try:
            if not obs.ensure():
                time.sleep(1.0)
                continue
            st = obs.states()
            now = time.time()

            if not booted:
                booted = True
                on = [n for n, v in st.items() if v]
                if len(on) > 1:
                    active = on[0]
                    active_until = now + DURATIONS[active] + TAIL_S
                    for extra in on[1:]:
                        obs.set_enabled(extra, False)
                        queue.append(extra)
                    log("boot: adopted %s, queued %s" % (active, on[1:]))
                    continue
                if len(on) == 1:
                    active = on[0]
                    active_until = now + DURATIONS[active] + TAIL_S
                    log("boot: adopted %s as active" % active)
                    continue

            # 1) active play's time is up -> end it, start next.
            if active and now >= active_until:
                if st.get(active):
                    obs.set_enabled(active, False)
                log("end: %s" % active)
                active = None
                if queue:
                    nxt = queue.pop(0)
                    if obs.set_enabled(nxt, True):
                        active = nxt
                        active_until = now + DURATIONS[nxt] + TAIL_S
                        log("start (queued): %s" % nxt)
                continue

            # 2) active meme hidden early -> a stale deck hide landed.
            if active and not st.get(active, False):
                if obs.set_enabled(active, True):
                    log("corrected stale hide on active %s" % active)
                continue

            # 3) new arrivals.
            acted = False
            for name, is_on in st.items():
                if not is_on or name == active or name in queue:
                    continue
                if active is None:
                    active = name
                    active_until = now + DURATIONS[name] + TAIL_S
                    log("start: %s" % name)
                else:
                    obs.set_enabled(name, False)
                    queue.append(name)
                    log("queued: %s (behind %s)" % (name, active))
                acted = True
            if acted:
                continue
        except Exception as e:
            log("err loop %r" % (e,))
            obs.session = None
            time.sleep(0.5)
        time.sleep(POLL_S)


if __name__ == "__main__":
    main()
