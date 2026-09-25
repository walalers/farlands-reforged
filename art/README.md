# Art

## `farman_skin.png`

FarMan's skin: a standard 64×64 classic-model skin, pitch black with red eyes and a faint red smile
(the "Darkness of the Farlands" eyes and the "Farman" smile).

The mod adds no client-side assets, so FarMan's face reaches players as a player head whose texture
Mojang hosts on `textures.minecraft.net`. To get it there, the skin was uploaded to a Minecraft
account once (2026-09-24). The resulting texture hash,
`f9f9e13a62dbf086926be393981fbe8a12694d17e4e9b540e24b5222654d8a26`, is `SKIN_TEXTURE_HASH` in `FarMan.java`;
the hosted image is pixel-identical to this PNG. Mojang textures are
addressed by content, so the hash keeps working after that account changes its skin back.

To change his face: edit the PNG, upload it as a skin, read the new URL from
`https://sessionserver.mojang.com/session/minecraft/profile/<uuid>` (the `textures` property is
base64 JSON), and put the hash from the end of that URL into `SKIN_TEXTURE_HASH`.
