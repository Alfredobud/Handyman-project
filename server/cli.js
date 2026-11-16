'use strict';
// Gera um código de membro direto no servidor: npm run new-code -- "nota" [dias de validade]
// Rode com o servidor parado, ou use POST /admin/codes com o servidor no ar.
const { newCode } = require('./store');
const [note = '', days = '0'] = process.argv.slice(2);
console.log(newCode(note, +days || 0));
setTimeout(() => process.exit(0), 400);
