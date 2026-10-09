import assert from 'node:assert/strict';
import { wallTimeToUtc, zonedInput } from '../src/lib/time.ts';
assert.equal(wallTimeToUtc('2026-10-09T15:00','Asia/Almaty'),'2026-10-09T10:00:00.000Z');
assert.equal(wallTimeToUtc('2026-10-09T15:00','Asia/Bishkek'),'2026-10-09T09:00:00.000Z');
assert.equal(zonedInput('2026-10-09T23:30:00Z','Asia/Almaty'),'2026-10-10T04:30');
assert.equal(wallTimeToUtc('2026-10-09T15:00','Asia/Kathmandu'),'2026-10-09T09:15:00.000Z');
assert.throws(()=>wallTimeToUtc('2026-03-08T02:30','America/New_York'));
assert.throws(()=>wallTimeToUtc('2026-11-01T01:30','America/New_York'));
console.log('PASS: timezone conversion, date boundary, fractional offset, DST gaps and ambiguity');
