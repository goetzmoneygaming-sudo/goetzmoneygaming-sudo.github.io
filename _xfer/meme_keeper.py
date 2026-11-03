# -*- coding: utf-8 -*-
"""
meme_keeper.py -- the meme queue keeper (Nova, 2026-11-03).

Sam's rule: memes never overlap. The Fifine deck buttons fire
OBS Show + a timed Hide directly (one-shots). Two presses close
together would overlap -- the deck has no cross-button queue.
This keeper is that queue, enforced on the OBS side:

  * It watches the 11 meme items in the Memes scene (direct
    obs-websocket, ~0.15 s poll).
  * The first meme to appear becomes the ACTIVE play and runs its
    full duration (the same table the deck buttons use).
  * Any other meme that appears while one is active is hidden
    immediately and QUEUED (FIFO). When the active play ends, the
    keeper hides it (if the deck's own timer hasn't) and starts
    the next in line with a fresh full duration.
  * A deck button's stale Hide can land mid-play on a queued meme
    (it was scheduled from the press, not the play). Any hide of
    the ACTIVE meme before its scheduled end is undone at once --
    the stale timer fires only once, so one correction suffices.
  * At boot, a meme found already on is adopted as the active
    play with a fresh window (better than an autoplay free-for-all
    after an OBS restart).

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

# name -> seconds (ffprobe table, same one the deck one-shots use)
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
        out = {}
        for it in resp.get("sceneItems", []):
            name = it.get("sourceName")
            if name in DURATIONS:
                out[name] = bool(it.get("sceneItemEnabled"))
        return out

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
    log("start: meme queue keeper watching")
    active = None          # name of the meme currently playing
    active_until = 0.0
    queue = []             # FIFO of names waiting
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
                    keep = on[0]
                    for extra in on[1:]:
                        obs.set_enabled(extra, False)
                        queue.append(extra)
                    active, active_until = keep, now + DURATIONS[keep] + TAIL_S
                    log("boot: adopted %s as active, queued %s" % (keep, on[1:]))
                elif len(on) == 1:
                    active = on[0]
                    active_until = now + DURATIONS[active] + TAIL_S
                    log("boot: adopted %s as active" % active)

            # end of the active play?
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

            # watch for changes
            for name, is_on in st.items():
                if name == active:
                    if not is_on and active and now < active_until:
                        # someone else's stale hide landed mid-play
                        if obs.set_enabled(name, True):
                            log("corrected stale hide on active %s" % name)
                    continue
                if is_on and name not in queue:
                    if active is None:
                        active = name
                        active_until = now + DURATIONS[name] + TAIL_S
                        log("start: %s" % name)
                    else:
                        obs.set_enabled(name, False)
                        queue.append(name)
                        log("queued: %s (behind %s)" % (name, active))
        except Exception as e:
            log("err loop %r" % (e,))
            obs.session = None
            time.sleep(0.5)
        time.sleep(POLL_S)


if __name__ == "__main__":
    main()
