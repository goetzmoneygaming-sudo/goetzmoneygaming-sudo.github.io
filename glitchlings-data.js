/* ============================================================================
   GLITCHLINGS — page data (single source of truth for glitchlings.html)
   ----------------------------------------------------------------------------
   Roster (name / type / tier) mirrors SPECIES_INFO in the stream bot's
   battle.py. The public notes are distilled from canon-cards-v1.md, which is
   DRAFT canon — when the reconciled notes land, edit ONLY this file and the
   page updates itself. Rackshasa (Rare, CHROME) is intentionally absent: it
   has no card art.

   Card art lives at assets/glitchlings/<id>.png (same bare filenames as the
   bot's C:\Cache\assets\cards\<id>.png). Missing art falls back to a letter
   badge on the page automatically.

   Leaderboard rows: { viewer, wins, losses, ties, badges: ["First Win", ...] }.
   Leave GLITCHLING_LEADERBOARD empty until real battles have been fought —
   the page shows an honest empty state. Badges are awarded by all-time win
   count per GLITCHLING_BADGES below (Nova-proposed ladder, pending Sam's OK).
   ========================================================================== */

const GLITCHLINGS = [
  /* ---- COMMON ---- */
  { id: "pingsqueak", name: "Pingsqueak", type: "VOLT", tier: "Common", art: "assets/glitchlings/pingsqueak.png",
    note: "A cable-mouse the size of a thumbnail that travels the power rails in sparking hops — and answers any diagnostic ping sent through the machine before the router can. Cache's latency graphs all show a respondent that does not exist." },
  { id: "curslime", name: "Curslime", type: "PIXEL", tier: "Common", art: "assets/glitchlings/curslime.png",
    note: "A square-edged blob of spilled pixels sliding along the bottom of the screen, eating any cursor that slips off the edge. You can see three swallowed arrows inside it, suspended like fossils." },
  { id: "bittybat", name: "Bittybat", type: "STATIC", tier: "Common", art: "assets/glitchlings/bittybat.png",
    note: "A bat made entirely of television static that hangs from the antenna lead and navigates by interference. It flies best when the signal is at its worst — and startles hard at dead silence." },
  { id: "cachemunk", name: "Cachemunk", type: "DATA", tier: "Common", art: "assets/glitchlings/cachemunk.png",
    note: "A chipmunk with memory-buffer cheeks that hoards icons and thumbnails in hiding spots it immediately forgets. Half the 'lost' files on this machine are in a folder whose name is a single space." },
  { id: "fizzbyte", name: "Fizzbyte", type: "NEON", tier: "Common", art: "assets/glitchlings/fizzbyte.png",
    note: "One byte rendered as a drink — a translucent cube of eight bubbles that lives in the RGB light strip and takes the color of whatever lighting profile is running. Static purple keeps it calm. This is related." },
  { id: "trackpadger", name: "Trackpadger", type: "CHROME", tier: "Common", art: "assets/glitchlings/trackpadger.png",
    note: "A badger pressed flat out of a trackpad plate, burrowed between the drive bays, polishing everything it passes to a mirror. If the mouse sensitivity feels different some mornings, it is. One notch. Always one notch." },
  { id: "bitbloom", name: "Bitbloom", type: "NEON", tier: "Common", art: "assets/glitchlings/bitbloom.png",
    note: "A flower grown out of a screensaver, petals made of translucent windows, eating display light. It reaches full bloom exactly once a week — during the Sunday countdown, showing off for a timer." },
  { id: "pondbyte", name: "Pondbyte", type: "STATIC", tier: "Common", art: "assets/glitchlings/pondbyte.png",
    note: "A single byte floating in the liquid-cooling reservoir — the only open water in the machine. Once a night it sleeps on the pump intake and the whole loop runs exactly two degrees warmer." },
  { id: "encore", name: "Encore", type: "ECHO", tier: "Common", art: "assets/glitchlings/encore.png",
    note: "A speaker-cone creature that makes exactly one sound: the last sound it heard, repeated one beat late and slightly quieter. Never feed it applause — the loop has no natural end." },
  { id: "bootsect", name: "Bootsect", type: "DATA", tier: "Common", art: "assets/glitchlings/bootsect.png",
    note: "A six-legged insect with a cursor for an eye that lives in the first 512 bytes and inspects every boot, sector by sector, on foot. Slow boots here aren't failures. They're corrections." },
  { id: "dialtone", name: "Dialtone", type: "ECHO", tier: "Common", art: "assets/glitchlings/dialtone.png",
    note: "A coiled telephone cord with a handset head, humming 350 and 440 hertz since the machine first connected. Every ringtone in the stream audio makes it sit up, hopeful. The calls are never for it." },

  /* ---- UNCOMMON ---- */
  { id: "glitchpup", name: "Glitchpup", type: "GLITCH", tier: "Uncommon", art: "assets/glitchlings/glitchpup.png",
    note: "A dog built at a slightly wrong frame rate — one ear a missing-texture checkerboard, its bark a voice line at the wrong sample rate. It fetches deleted files out of the recycle bin and delivers them to Cache, proud. The bin refilling itself has always been the dog." },
  { id: "mothboard", name: "Mothboard", type: "ECHO", tier: "Uncommon", art: "assets/glitchlings/mothboard.png",
    note: "A moth with circuit-trace wings that sleeps flat on the motherboard, camouflaged by honesty. Alert banners arrive with small bites out of the corners. Viewers assume it's the design. It is not the design." },
  { id: "mainlet", name: "Mainlet", type: "VOLT", tier: "Uncommon", art: "assets/glitchlings/mainlet.png",
    note: "A piglet built from a power brick that snacks on stray voltage and glows notch by notch as it fills. The night the power flickered mid-stream, the rail held for eleven extra seconds. The notches were empty afterward." },
  { id: "perfora", name: "Perfora", type: "DATA", tier: "Uncommon", art: "assets/glitchlings/perfora.png",
    note: "A ribbon creature in the shape of punched tape, feeding itself through vents one hole at a time. The holes near its head spell the machine's first-ever boot log. It walks around wearing day one." },
  { id: "cathermit", name: "Cathermit", type: "STATIC", tier: "Uncommon", art: "assets/glitchlings/cathermit.png",
    note: "A static-fuzz hermit housed in a GPU backplate, trading up shells as it grows. Nobody has ever seen it between shells — the entire photographic record is one frame of motion blur, filed under portraits." },
  { id: "tapeloop", name: "Tapeloop", type: "ECHO", tier: "Uncommon", art: "assets/glitchlings/tapeloop.png",
    note: "A body of magnetic tape on spool feet. Everything it hears returns eight seconds later with tape hiss — including one protected splice holding the channel's first-ever 'hello chat.' That part is a monument." },
  { id: "pipedream", name: "Pipedream", type: "NEON", tier: "Uncommon", art: "assets/glitchlings/pipedream.png",
    note: "A glowing wisp running an endless route through the screensaver pipes — 214 joints, same order, every night. Its whole world only exists while the display sleeps, and it has never once complained." },
  { id: "stackquack", name: "Stackquack", type: "DATA", tier: "Uncommon", art: "assets/glitchlings/stackquack.png",
    note: "A duck assembled from stacked error dialogs, one new window per crash, with two OK buttons for eyes. It has never been clicked. When it quacks, the ding is modal — everything waits." },
  { id: "lowbatt", name: "Lowbatt", type: "VOLT", tier: "Uncommon", art: "assets/glitchlings/lowbatt.png",
    note: "A battery-icon creature that has run at 15% for three years. It is not dying; it is conserving. Every low-power warning in the machine's logs is just Lowbatt saying hello, daily, into the record." },
  { id: "joyrider", name: "Joyrider", type: "CHROME", tier: "Uncommon", art: "assets/glitchlings/joyrider.png",
    note: "A pocket hot-rod in a game-controller shell, time-trialing the chassis rails on fan-bearing wheels. Its standing lap record is eleven seconds, set with a fan tailwind it refuses to asterisk." },

  /* ---- RARE ---- */
  { id: "mintmark", name: "Mintmark", type: "MINT", tier: "Rare", art: "assets/glitchlings/mintmark.png",
    note: "A GM Credit token that got up and walked — a flawless mint coin that refuses circulation. It has reached the front of the spend queue nine hundred times and stepped aside nine hundred times. The channel's coin sound was sampled from its footsteps." },
  { id: "overstack", name: "Overstack", type: "GLITCH", tier: "Rare", art: "assets/glitchlings/overstack.png",
    note: "A wobbling tower of duplicated windows, each layer a copy of the one beneath with exactly one detail wrong. Once it stacked to the top of its address space and saw the kernel. Since then it stacks more quietly." },
  { id: "motherwyrm", name: "Motherwyrm", type: "DATA", tier: "Rare", art: "assets/glitchlings/motherwyrm.png",
    note: "A great wyrm whose body is a chain of linked directories, tunneling the archive and leaving every file contiguous behind it. Every file on this machine has passed through her tunnels exactly once. She is the road the oldest things travel." },
  { id: "testcard", name: "Testcard", type: "NEON", tier: "Rare", art: "assets/glitchlings/testcard.png",
    note: "A living test pattern standing upright in the broadcast standby buffer, color bars up, tone ready. It owns the highest total screen time in the machine — half a second at a time, between scenes, in the gap nobody watches." }
];

/* All-time win-count badge ladder (Nova-proposed names — Sam to approve). */
const GLITCHLING_BADGES = [
  { wins: 1,  name: "First Win" },
  { wins: 5,  name: "On a Roll" },
  { wins: 10, name: "Arena Regular" },
  { wins: 25, name: "Storm Circuit" },
  { wins: 50, name: "Living Legend" }
];

/* Battle leaderboard — empty until real battles have been fought. No fake entries.
   Row shape: { viewer: "name", wins: 0, losses: 0, ties: 0, badges: ["First Win"] } */
const GLITCHLING_LEADERBOARD = [];
