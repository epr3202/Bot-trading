// Optional local browser check using an installed Chromium; no downloaded browser/driver.
import { spawn } from 'node:child_process';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const browserPath = process.argv[2];
if (!browserPath) throw new Error('Provide the installed Chromium executable path');
const runtime = resolve('runtime');
await mkdir(runtime, { recursive: true });
const browser = spawn(browserPath, [
  '--headless=new', '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=9227',
  '--disable-background-networking', '--disable-component-update', '--no-first-run',
  '--no-default-browser-check', '--disable-sync', '--disable-extensions',
  '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE 127.0.0.1',
  `--user-data-dir=${resolve(runtime, 'browser-check-profile')}`, 'http://127.0.0.1:8765',
], { windowsHide: true, stdio: 'ignore' });
const pause = ms => new Promise(done => setTimeout(done, ms));
let socket;
try {
  let pages;
  for (let i = 0; i < 60; i++) {
    try { pages = await (await fetch('http://127.0.0.1:9227/json')).json(); if (pages.some(p => p.type === 'page')) break; }
    catch { /* browser initialization */ }
    await pause(200);
  }
  const page = pages?.find(p => p.type === 'page');
  if (!page) throw new Error('Local browser debugging did not start');
  socket = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((done, reject) => { socket.addEventListener('open', done, { once:true }); socket.addEventListener('error', reject, { once:true }); });
  let serial = 0;
  const pending = new Map();
  socket.addEventListener('message', event => { const message = JSON.parse(event.data); if (pending.has(message.id)) { const [done, reject] = pending.get(message.id); pending.delete(message.id); message.error ? reject(new Error(message.error.message)) : done(message.result); } });
  const send = (method, params={}) => new Promise((done,reject) => { const id=++serial; pending.set(id,[done,reject]); socket.send(JSON.stringify({id,method,params})); });
  const evaluate = async expression => {
    const result = await send('Runtime.evaluate', {expression, awaitPromise:true, returnByValue:true});
    if (result.exceptionDetails) throw new Error('Browser JavaScript exception');
    return result.result.value;
  };
  await send('Emulation.setDeviceMetricsOverride', {width:1440,height:1100,deviceScaleFactor:1,mobile:false});
  await send('Page.enable');
  for(let i=0;i<50;i++){ if(await evaluate("Boolean(document.getElementById('login-form'))")) break; await pause(100); }
  const token = (await readFile(resolve(runtime,'control-token'),'utf8')).trim();
  await evaluate(`document.getElementById('token').value=${JSON.stringify(token)}; document.getElementById('login-form').requestSubmit();`);
  for(let i=0;i<100;i++){ if(await evaluate("document.getElementById('login').hidden")) break; await pause(100); }
  const state = await evaluate("({authenticated:document.getElementById('login').hidden,mode:document.getElementById('mode').textContent,orders:document.getElementById('order-count').textContent,feedback:document.getElementById('feedback').textContent})");
  if (!state.authenticated || state.mode !== 'OFFLINE' || Number(state.orders) < 4) throw new Error('Dashboard state verification failed');
  const layout = await send('Page.getLayoutMetrics');
  const shot = await send('Page.captureScreenshot', {format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:1440,height:Math.ceil(layout.cssContentSize.height),scale:1}});
  await writeFile(resolve(runtime,'dashboard.png'), Buffer.from(shot.data,'base64'));
  await writeFile(resolve(runtime,'browser-evidence.json'), JSON.stringify({...state,screenshot:'runtime/dashboard.png'},null,2));
  process.stdout.write(JSON.stringify({...state,screenshot:'runtime/dashboard.png'})+'\n');
  await send('Browser.close').catch(()=>{});
} finally {
  socket?.close();
  browser.kill();
}
