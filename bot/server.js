// bot/server.js
const mineflayer = require('mineflayer');
const WebSocket = require('ws');

const HOST = 'localhost';   // your Minecraft server host
const PORT = 25565;         // your Minecraft server port
const USERNAME = 'MACL_BOT'; // offline mode username

// --- 1) Create Mineflayer bot ---
const bot = mineflayer.createBot({
  host: HOST,
  port: PORT,
  username: USERNAME,
  version: '1.21.1' // <-- Manually add this line to force a stable version
});
// Simulated threat flag (we'll trigger from Python)
let threatActive = false;
let executing = false; 
let queue = []; // Make sure your queue is defined here too if it isn't already
// Reflex action: simple "run backward" for 1 second

async function reflexEvasiveAction() {
  bot.chat('Reflex: evasive action triggered!');
  try {
    bot.setControlState('back', true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
  } finally {
    bot.setControlState('back', false);
  }
}

// Parse a simple MAC-L-like envelope: "BATCH 1 DO MOVE 1 0 0 DO CHAT hello END"
function parseMaclEnvelope(raw) {
  raw = raw.trim();
  if (!raw.startsWith('BATCH') || !raw.endsWith('END')) {
    throw new Error('ERR_INVALID_ENVELOPE');
  }

  const parts = raw.split(/\s+/);
  if (parts.length < 4) {
    throw new Error('ERR_SHORT_ENVELOPE');
  }

  // BATCH <id> DO ...
  const taskId = parts[1];
  const actions = [];

  let i = 3; // index after "BATCH <id> DO"
  while (i < parts.length) {
    const token = parts[i];
    if (token === 'END') break;
    const opcode = token;
    i += 1;
    const args = [];
    while (i < parts.length && parts[i] !== 'DO' && parts[i] !== 'END') {
      args.push(parts[i]);
      i += 1;
    }
    actions.push({ opcode, args });
    if (parts[i] === 'DO') i += 1;
  }

  return { taskId, actions };
}

// Execute a single action against Mineflayer
async function executeAction(action) {
  const { opcode, args } = action;

  if (opcode === 'CHAT') {
    const msg = args.join(' ');
    bot.chat(msg);
  } else if (opcode === 'WAIT') {
    const ms = parseInt(args[0] || '500', 10);
    await new Promise((resolve) => setTimeout(resolve, ms));
  } else if (opcode === 'MOVE') {
    // MOVE dx dy dz over 1 second (very simplified)
    const dx = parseFloat(args[0] || '0');
    const dy = parseFloat(args[1] || '0');
    const dz = parseFloat(args[2] || '0');
    const pos = bot.entity.position.clone().offset(dx, dy, dz);
    bot.chat(`Moving toward ${pos.x.toFixed(1)} ${pos.y.toFixed(1)} ${pos.z.toFixed(1)}`);
    await new Promise((resolve) => setTimeout(resolve, 1000));
  } else {
    bot.chat(`Unknown opcode: ${opcode}`);
  }
}

// Main executor loop
async function runQueue(taskId) {
  if (executing) return;
  executing = true;

  const startTime = Date.now();
  let completedSteps = 0;

  try {
    for (let i = 0; i < currentQueue.length; i++) {
      if (threatActive) {
        // L0: wipe queue
        const wipedSteps = currentQueue.length - i;
        currentQueue = [];

        // L1: reflex
        const interruptTime = Date.now();
        await reflexEvasiveAction();
        const reflexDone = Date.now();

        // send INT envelope back
        const interruptEnvelope = {
          type: 'INT',
          taskId,
          completedSteps,
          totalSteps: completedSteps + wipedSteps,
          interruptMs: reflexDone - startTime,
          reflexMs: reflexDone - interruptTime,
        };
        if (wsClient) {
          wsClient.send(JSON.stringify(interruptEnvelope));
        }

        threatActive = false;
        executing = false;
        return;
      }

      await executeAction(currentQueue[i]);
      completedSteps += 1;
    }

    const endTime = Date.now();
    const resultEnvelope = {
      type: 'RESULT',
      taskId,
      status: 'DONE',
      completedSteps,
      totalSteps: completedSteps,
      latencyMs: endTime - startTime,
    };
    if (wsClient) {
      wsClient.send(JSON.stringify(resultEnvelope));
    }
  } catch (err) {
    const endTime = Date.now();
    const resultEnvelope = {
      type: 'RESULT',
      taskId,
      status: 'ERROR',
      error: String(err),
      completedSteps,
      totalSteps: currentQueue.length,
      latencyMs: endTime - startTime,
    };
    if (wsClient) {
      wsClient.send(JSON.stringify(resultEnvelope));
    }
  } finally {
    executing = false;
    currentQueue = [];
  }
}

// --- 3) WebSocket server for MAC-L envelopes & threats ---
const wss = new WebSocket.Server({ port: 8765 }, () => {
  console.log('MAC-L WebSocket server listening on ws://localhost:8765');
});

wss.on('connection', (ws) => {
  console.log('Python controller connected');
  wsClient = ws;

  ws.on('message', async (message) => {
    const msg = message.toString().trim();

    // Protocol:
    //   - JSON {"type": "THREAT"} to trigger interrupt
    //   - plain text MAC-L envelope for execution
    try {
      if (msg.startsWith('{')) {
        const obj = JSON.parse(msg);
        if (obj.type === 'THREAT') {
          console.log('Received THREAT from controller');
          threatActive = true;
          return;
        }
      } else {
        // Treat as MAC-L envelope
        console.log('Received envelope:', msg);
        const parsed = parseMaclEnvelope(msg);
        currentQueue = parsed.actions;
        runQueue(parsed.taskId);
      }
    } catch (err) {
      console.error('Error handling message:', err);
    }
  });

  ws.on('close', () => {
    console.log('Python controller disconnected');
    wsClient = null;
  });
});

bot.on('spawn', () => {
  console.log('Bot spawned in the world.');
});