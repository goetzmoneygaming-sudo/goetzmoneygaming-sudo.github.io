# -*- coding: utf-8 -*-
"""
wiring_listener.py -- the chat-trigger layer for the Glitchlings
wiring engine (Nova, 2026-11-02 night wiring session).

Streamer.bot command actions write small trigger files (the same
pattern the roast pipeline uses); this listener consumes them and
drives the engine:

  catch.txt    "%user%"               -> !save: attempt a catch
  trade.txt    "%user%|%rawInput%"    -> !trade @target myitem theiritem
  accept.txt   "%user%"               -> !accept (the trade target)
  decline.txt  "%user%"               -> !decline (the trade target)

Chat announcements ride one file + one poked Streamer.bot action
("Wiring Announce", C# reads the file, Send Message speaks as the
bot) -- the relay's poke pattern.

Fail-closed throughout: a malformed trigger is logged and dropped;
a trade that fails the ledger's checks announces the reason and
changes nothing. One open displayed offer is tracked so an expired
offer clears its screen.

Registered as a CacheStack proc. Log: wiring_listener.log.
"""
import json
import os
import sys
import time
import urllib.request

CD = r"C:\Cache"
WIRING = os.path.join(CD, "wiring")
TRIG = os.path.join(WIRING, "triggers")
LOG = os.path.join(WIRING, "wiring_listener.log")
ANNOUNCE_FILE = os.path.join(WIRING, "announce.txt")
CARDS_DIR = os.path.join(CD, "cards")
LEDGER_PATH = os.path.join(WIRING, "ledger.json")
SB_DO = "http://127.0.0.1:7474/DoAction"
POLL_S = 0.35
CATCH_COOLDOWN_S = 45          # per-viewer !save cooldown (tunable)

sys.path.insert(0, WIRING)
import ledger as ledger_mod      # noqa: E402
import senders                   # noqa: E402


def log(m):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%H:%M:%S ") + m + "\n")
    except OSError:
        pass


def pfp_for(user):
    """A loadable profile-picture URL for the trade screen. Public
    avatar redirect; if it ever fails the page fails closed (the
    trade still completes in the ledger and announces in chat)."""
    return "https://decapi.me/twitch/avatar/" + user


def announce(text):
    try:
        with open(ANNOUNCE_FILE, "w", encoding="utf-8") as f:
            f.write(text)
        body = json.dumps({"action": {"name": "Wiring Announce"}}).encode()
        req = urllib.request.Request(SB_DO, data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            resp.read()
        log("announce: " + text)
    except Exception as e:
        log("announce failed %r (%s)" % (e, text))


def take(path):
    """Read + delete a trigger file; returns its content or None."""
    try:
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            content = f.read().strip().lstrip("\ufeff")
        os.remove(path)
        return content
    except OSError:
        return None


def resolve_item(token):
    t = token.strip().lower().replace(" ", "")
    if t in ledger_mod.CARD_IDS:
        return {"kind": "card", "id": t}
    if t in ledger_mod.SPECIES:
        return {"kind": "creature", "id": t}
    return None


class Listener:
    def __init__(self):
        self.ledger = ledger_mod.Ledger(state_path=LEDGER_PATH,
                                        cards_dir=CARDS_DIR)
        self.catch_cool = {}        # user -> last catch time
        self.shown_offer = None     # offer dict currently on screen
        self.shown_until = 0.0

    # -- catch ------------------------------------------------------
    def do_catch(self, user):
        user = ledger_mod.norm_user(user)
        if not user:
            return
        now = time.time()
        last = self.catch_cool.get(user, 0)
        if now - last < CATCH_COOLDOWN_S:
            log("catch: %s on cooldown" % user)
            return
        self.catch_cool[user] = now
        try:
            res = senders.attempt_catch(self.ledger, CD, user)
            log("catch: %(user)s -> %(species)s (%(tier)s) success=%(success)s shiny=%(shiny)s"
                % dict(res, user=user))
        except Exception as e:
            log("catch error for %s: %r" % (user, e))

    # -- trades -----------------------------------------------------
    def find_offer_for(self, user):
        user = ledger_mod.norm_user(user)
        for off in self.ledger.data.get("offers", []):
            if user in (off["from"], off["to"]):
                return off
        return None

    def show_offer(self, offer, stage):
        a, b = senders.trade_sides(self.ledger, offer, pfp_for)
        senders.fire_trade(CD, offer["id"], stage, a, b)
        if stage == "offer":
            self.shown_offer = offer
            self.shown_until = offer["expires"]
        elif stage == "gone":
            self.shown_offer = None

    def do_trade(self, content):
        try:
            user, raw = content.split("|", 1)
        except ValueError:
            log("trade: malformed trigger %r" % content)
            return
        user = ledger_mod.norm_user(user)
        toks = raw.replace("!", " ").split()
        toks = [t for t in toks if t.lower() != "trade"]
        if len(toks) < 3:
            announce("Trade usage: !trade @viewer <your card or creature> <their card or creature>")
            return
        target = ledger_mod.norm_user(toks[0].lstrip("@"))
        give = resolve_item(toks[1])
        want = resolve_item(toks[2])
        if give is None or want is None:
            announce("Trade failed: I don't know one of those cards/creatures. Names are the Series 1 names, one word each.")
            return
        try:
            offer = self.ledger.open_trade(user, target, give, want)
        except ValueError as e:
            announce("Trade failed: %s" % e)
            log("trade open failed (%s -> %s): %s" % (user, target, e))
            return
        self.show_offer(offer, "offer")
        announce("@%s — %s wants to trade their %s for your %s. Type !accept or !decline within 60 seconds."
                 % (target, user, give["id"], want["id"]))
        log("trade open %s: %s gives %s, wants %s from %s"
            % (offer["id"], user, give["id"], want["id"], target))

    def do_accept(self, user):
        user = ledger_mod.norm_user(user)
        offer = self.find_offer_for(user)
        if not offer:
            return
        if offer["to"] != user:
            log("accept: %s tried to accept an offer addressed to %s"
                % (user, offer["to"]))
            return
        try:
            done = self.ledger.accept_trade(offer["id"])
        except ValueError as e:
            self.show_offer(offer, "gone")
            announce("Trade fell through: %s" % e)
            log("trade accept failed: %s" % e)
            return
        self.show_offer(done, "complete")
        announce("Trade complete: %s's %s for %s's %s. Cache has updated both binders."
                 % (done["from"], done["give"]["id"], done["to"], done["want"]["id"]))
        log("trade complete %s" % done["id"])
        time.sleep(3.5)
        self.show_offer(done, "gone")

    def do_decline(self, user):
        user = ledger_mod.norm_user(user)
        offer = self.find_offer_for(user)
        if not offer:
            return
        if user not in (offer["to"], offer["from"]):
            return
        try:
            self.ledger.decline_trade(offer["id"])
        except ValueError as e:
            log("decline failed: %s" % e)
            return
        self.show_offer(offer, "gone")
        announce("Trade declined. The %s stays where it is." % offer["give"]["id"])
        log("trade declined %s by %s" % (offer["id"], user))

    # -- expiry watch ----------------------------------------------
    def tick_expiry(self):
        if self.shown_offer and time.time() > self.shown_until:
            off = self.shown_offer
            self.shown_offer = None
            try:
                senders.fire_trade(CD, off["id"], "gone",
                                   *senders.trade_sides(self.ledger, off, pfp_for))
            except Exception:
                pass
            announce("That trade offer expired. Run it back with !trade if you still want it.")
            log("trade expired %s" % off["id"])

    # -- main loop ---------------------------------------------------
    def run(self):
        os.makedirs(TRIG, exist_ok=True)
        log("start: watching triggers in %s" % TRIG)
        while True:
            try:
                c = take(os.path.join(TRIG, "catch.txt"))
                if c:
                    self.do_catch(c)
                t = take(os.path.join(TRIG, "trade.txt"))
                if t:
                    self.do_trade(t)
                a = take(os.path.join(TRIG, "accept.txt"))
                if a:
                    self.do_accept(a)
                d = take(os.path.join(TRIG, "decline.txt"))
                if d:
                    self.do_decline(d)
                self.tick_expiry()
            except Exception as e:
                log("loop error %r" % (e,))
            time.sleep(POLL_S)


if __name__ == "__main__":
    Listener().run()
