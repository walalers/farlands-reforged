// A headless player for the FarMan test: joins an offline-mode server and reports what it sees.
//
//   node tools/farman_bot.cjs <host> <port> <minecraft-version> [username]
//
// FarMan only exists while a real player is in the Far Lands, so a server test needs somebody logged in.
// This is that somebody. It does nothing on its own; farman_test.py drives it over RCON (teleports, turns
// its head, runs commands as it), and this prints one JSON line per thing worth knowing - spawned, chat
// and system messages, effects applied to it, kicked - for the test to read.
//
// Needs mineflayer, installed outside the repository:
//   npm install --prefix ~/.cache/farlands-server-test/node mineflayer
// and NODE_PATH pointing at that node_modules (farman_test.py sets it). It is .cjs so that Node treats it as
// CommonJS whatever package.json sits above the repository.

const mineflayer = require('mineflayer')

const [host, port, version, username = 'FarBot'] = process.argv.slice(2)

function emit (event, fields = {}) {
  process.stdout.write(JSON.stringify({ event, ...fields }) + '\n')
}

const bot = mineflayer.createBot({
  host,
  port: Number(port),
  version,
  username,
  auth: 'offline',
  hideErrors: false
})

// minecraft-protocol reads the server's command tree to sign chat commands, and hangs up on a tree it cannot
// validate - Forge 1.21.6 sends one. This bot never types a command, so it does not need the tree at all.
// The listener is attached after createBot returns, and the tree arrives after login, so remove it there.
bot.once('login', () => bot._client.removeAllListeners('declare_commands'))

bot.once('spawn', () => emit('spawn', { position: bot.entity.position }))
bot.on('message', (message, position) => emit('message', { text: message.toString(), position }))
bot.on('entityEffect', (entity, effect) => {
  if (entity === bot.entity) emit('effect', { id: effect.id, amplifier: effect.amplifier, duration: effect.duration })
})
bot.on('forcedMove', () => emit('moved', { position: bot.entity.position, yaw: bot.entity.yaw, pitch: bot.entity.pitch }))
bot.on('kicked', (reason) => emit('kicked', { reason: typeof reason === 'string' ? reason : JSON.stringify(reason) }))
bot.on('error', (err) => emit('error', { message: String(err && err.message ? err.message : err) }))
bot.on('end', (reason) => { emit('end', { reason: String(reason) }); process.exit(0) })

// Commands from farman_test.py, one JSON object per line on stdin. Turning the head has to happen here: a
// server-side `tp ... facing` is overwritten by the next rotation the client sends.
//   {"lookAt": [x, y, z]}   turn to look at a point, and report the new rotation
// Closing stdin stops the bot.
const { Vec3 } = require('vec3')
require('readline').createInterface({ input: process.stdin }).on('line', (line) => {
  let command
  try { command = JSON.parse(line) } catch (err) { return emit('error', { message: `bad command: ${line}` }) }
  if (command.lookAt) {
    bot.lookAt(new Vec3(...command.lookAt), true)
      .then(() => emit('looked', { yaw: bot.entity.yaw, pitch: bot.entity.pitch }))
      .catch((err) => emit('error', { message: String(err) }))
  }
}).on('close', () => { bot.quit(); setTimeout(() => process.exit(0), 2000) })
