# JengChat — Friends Testing

Public Windows downloads and the friends-win-x64 update channel. Source: https://github.com/mattarm555/JengChat

Build friends draft accepts a reviewed source tag. Publish tested friends release requires the completed two-machine pilot. No releases are automatic. No private credentials are distributed. The public page is https://mattarm555.github.io/JengChat-downloads/

## From 3.0.0: the Godot client

Build friends draft now builds the Godot client (`client-godot/tools/build_release.py` in the source tag), with pinned Godot 4.7.2 mono and export templates (`client-godot/tools/setup_godot.py`). Before creating the draft it runs the unchanged publisher on the built files (`tools/check_draft.py`), so a release the publish workflow would reject never becomes a draft. The package id, channel and feed are the same as 2.x (`JengChat.Friends`, `friends-win-x64`, `/updates/`), so installed 2.x copies are offered 3.0.0 as a normal update. The pilot (PILOT.md) is that update on a friend's machine: 2.1.0-beta.6 to 3.0.0-beta.1.

## JengParty (`party/`)

JengParty is a separate game with its own private source repository (`mattarm555/JengParty`). It is published here too, so friends can download it, and JengChat will install it with one click (JengParty's `DISTRIBUTION.md`).

- **Tags:** JengParty releases are tagged `party-v<version>`, so they never clash with JengChat's `v<version>`.
- **Package:** `JengParty`, channel `party-win-x64`. Its feed is `/party/`.
- **Build JengParty draft** (`draft-party.yml`):
  - checks out a reviewed `party-v…` tag that is merged into JengParty's `main`;
  - copies the avatar models from the JengChat commit that JengParty's `shared/jengchat/SOURCE.md` names, and they must match the digest recorded there;
  - runs JengParty's rules and release checks;
  - builds with `tools/build_release.py`;
  - names the installer `JengParty-setup.exe`;
  - runs the real publisher on the files (`tools/check_draft.py --party`);
  - only then creates a draft prerelease.
- **Publish tested JengParty release** (`publish-party.yml`):
  - needs the second-machine pilot to have passed, and no JengParty waiver exists;
  - publishes the draft and redeploys the whole site.
- **The site:** it is one Pages deployment for both games.
  - Publishing JengChat keeps the live JengParty release, and publishing JengParty keeps the live JengChat release. Whatever is kept is fetched and verified again from its release assets.
  - `party/` holds:
    - `source.txt` and `releases.party-win-x64.json`: JengParty's update feed;
    - `release.json`: tag, version, installer URL, SHA-256, size, notes and acceptance. This is what JengChat's Get JengParty button reads.
  - Before the first JengParty release there is no `party/` folder, and the site is unchanged.

## The page (`site/`)

The page is static: `index.html`, `style.css`, `app.js`, self-hosted fonts in `site/fonts/` and app screenshots in `site/img/`. Screenshots come only from the client's demo and presentation runs (`--lounge-shot --lounge-demo`, `--chess-shot`, `tests/*Presentation`), with made-up names. `app.js` reads `release.json` (written by `tools/publish_delivery.py`) and accepts installer and release links only from this repository's releases. The design rules are in `DESIGN.md`.

### Live status panel

The Lounge section has an "In the Lounge right now" panel. It stays in its "Not connected" state until `<meta name="jengchat-status">` in `site/index.html` names a feed. The feed must be an `https://` URL (or a same-origin path) that allows cross-origin GET from the Pages site and returns:

```json
{"server": "online", "players": ["amy", "bob"], "updated": "2026-11-22T17:30:00Z"}
```

`server` is `online` or `offline`, `players` holds up to 60 account names of at most 32 characters (or `null` when the server answered but the list didn't), and `updated` is when the feed was last refreshed (the page marks data older than five minutes as possibly out of date). The page polls every 30 seconds while it is visible. The game server's `STATUS|<token>` query needs a secret token, so the browser never talks to the game server directly: something trusted has to publish this JSON.

The feed is served by JengBot (`mattarm555/discordBotGoogle2`, `cogs/server_status.py`) on the owner's PC `jengcomputer`: the bot checks the game server every minute and serves the result at `http://127.0.0.1:8790/jengchat-status.json`, which Tailscale Funnel publishes as `https://jengcomputer.tailc57584.ts.net:8443/jengchat-status.json`. When that PC or the bot is off, the panel says "Status unavailable".
