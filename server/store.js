'use strict';
// Persistência simples em arquivo JSON (códigos de membro, chat, trials).
// Suficiente para um servidor único; troque por um banco quando crescer.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const DIR = process.env.DATA_DIR || path.join(__dirname, '..', 'data');
const FILE = path.join(DIR, 'db.json');
fs.mkdirSync(DIR, { recursive: true });

let db = { secret: '', admin_token: '', codes: {}, chat: [], chat_seq: 0, names: {}, trials: {}, default_layers: null };
try { db = Object.assign(db, JSON.parse(fs.readFileSync(FILE, 'utf8'))); } catch (e) { /* primeiro boot */ }

let timer = null;
function save() {
  if (timer) return;
  timer = setTimeout(() => {
    timer = null;
    const tmp = FILE + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(db));
    fs.renameSync(tmp, FILE);
  }, 200);
}

if (!db.secret) { db.secret = crypto.randomBytes(32).toString('hex'); save(); }

const sha = (s) => crypto.createHash('sha256').update(db.secret + ':' + s).digest('hex').slice(0, 32);

/** Gera um código de membro legível (ex.: ATL-7K2M-9QXD). Guardamos só o hash. */
function newCode(note = '', days = 0) {
  const abc = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  const part = () => Array.from(crypto.randomBytes(4), (b) => abc[b % abc.length]).join('');
  const code = `ATL-${part()}-${part()}`;
  db.codes[sha(code)] = { note: String(note).slice(0, 80), created: new Date().toISOString(), expires: days > 0 ? Date.now() + days * 864e5 : 0, revoked: false };
  save();
  return code;
}

function checkCode(code) {
  const id = sha(String(code || '').trim().toUpperCase());
  const c = db.codes[id];
  if (!c || c.revoked || (c.expires && c.expires < Date.now())) return null;
  return id;
}

module.exports = { db, save, sha, newCode, checkCode, DIR };
