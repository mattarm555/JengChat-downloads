# JengChat — Friends Testing

Public Windows downloads and the friends-win-x64 update channel. Source: https://github.com/mattarm555/JengChat

Build friends draft accepts a reviewed source tag. Publish tested friends release requires the completed two-machine pilot. No releases are automatic. No private credentials are distributed. The public page is https://mattarm555.github.io/JengChat-downloads/

## From 3.0.0: the Godot client

Build friends draft now builds the Godot client (`client-godot/tools/build_release.py` in the source tag), with pinned Godot 4.7.2 mono and export templates (`client-godot/tools/setup_godot.py`). Before creating the draft it runs the unchanged publisher on the built files (`tools/check_draft.py`), so a release the publish workflow would reject never becomes a draft. The package id, channel and feed are the same as 2.x (`JengChat.Friends`, `friends-win-x64`, `/updates/`), so installed 2.x copies are offered 3.0.0 as a normal update. The pilot (PILOT.md) is that update on a friend's machine: 2.1.0-beta.6 to 3.0.0-beta.1.
