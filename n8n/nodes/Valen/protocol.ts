export type Question = { name: string; type: string; instructions: string; choices?: {value: string; description: string}[]; levels?: {label: string; description: string}[] };
export function baseUrl(value: string): string {
 const url = new URL(value);
 if (!['http:', 'https:'].includes(url.protocol) || url.search || url.hash || url.username || url.password) throw new Error('Base URL must be an HTTP(S) URL without credentials, query or fragment');
 return value.replace(/\/+$/, '').replace(/\/v1$/, '') + '/v1';
}
export function options(text: string): {value: string; description: string}[] {
 const rows = text.split('\n').map(s => s.trim()).filter(Boolean).map(line => {
  const at = line.indexOf(': '); const value = (at < 0 ? line : line.slice(0, at)).trim();
  const description = at < 0 ? value : line.slice(at + 2).trim();
  if (!value || !description) throw new Error('Options and descriptions must not be empty');
  return {value, description};
 });
 if (rows.length < 2 || new Set(rows.map(r => r.value)).size !== rows.length) throw new Error('Use at least two distinct options or levels');
 return rows;
}
export function questions(value: unknown): Question[] {
 const rows = typeof value === 'string' ? JSON.parse(value) : value;
 if (!Array.isArray(rows) || rows.length < 1) throw new Error('Use a nonempty questions array');
 const names = new Set();
 for (const q of rows) {
  if (!q || typeof q.name !== 'string' || !/^[A-Za-z0-9_]+$/.test(q.name) || names.has(q.name)) throw new Error('Question IDs must be unique letters, digits or underscores');
  names.add(q.name);
  if (typeof q.instructions !== 'string' || !q.instructions.trim()) throw new Error('Each question needs instructions');
  if (!['predicate','choice','score'].includes(q.type)) throw new Error('Question type must be predicate, choice or score');
  if (q.type !== 'predicate') {
   const list = q.type === 'choice' ? q.choices : q.levels;
   const key = q.type === 'choice' ? 'value' : 'label';
   if (!Array.isArray(list) || list.length < 2 || list.some(r => !r || typeof r[key] !== 'string' || !r[key].trim() || typeof r.description !== 'string' || !r.description.trim()) || new Set(list.map(r => r[key])).size !== list.length) throw new Error('Use at least two distinct, described choices or levels');
  }
 }
 return rows;
}
function probability(value: unknown): number {
 if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > 1) throw new Error('API returned an invalid probability');
 return value;
}
export function answers(response: any, asked: Question[]): Record<string, any> {
 if (!Array.isArray(response?.answers) || response.answers.length !== asked.length) throw new Error('API returned a missing or incomplete answer list');
 const result: Record<string, any> = Object.create(null);
 for (const q of asked) {
  const matches = response.answers.filter((a: any) => a.name === q.name);
  if (matches.length !== 1) throw new Error(`API did not return exactly one answer for ${q.name}`);
  const a = matches[0];
  if (a.type !== q.type) throw new Error(`API returned the wrong answer type for ${q.name}`);
  if (q.type === 'predicate') { result[q.name] = {probability: probability(a.probability)}; continue; }
  const key = q.type === 'choice' ? 'value' : 'label';
  const expected = (q.type === 'choice' ? q.choices! : q.levels!).map((r: any) => r[key]);
  if (!Array.isArray(a.probabilities) || a.probabilities.length !== expected.length) throw new Error('API returned incomplete candidate probabilities');
  const distribution: Record<string, number> = Object.create(null);
  for (const p of a.probabilities) {
   if (!expected.includes(p[key]) || Object.hasOwn(distribution, p[key])) throw new Error('API returned unknown or duplicate candidates');
   distribution[p[key]] = probability(p.probability);
  }
  if (Math.abs(Object.values(distribution).reduce((s,p) => s+p,0)-1) > 0.001) throw new Error('API probabilities do not sum to one');
  const confidence = probability(a.confidence);
  if (q.type === 'choice') {
   if (!expected.includes(a.choice)) throw new Error('API returned an unknown choice');
   result[q.name] = {choice:a.choice, confidence, probabilities:distribution};
  } else {
   if (typeof a.score !== 'number' || !Number.isFinite(a.score) || a.score < 0 || a.score > expected.length-1) throw new Error('API returned an invalid score');
   const level = expected.reduce((best, label) => distribution[label] > distribution[best] ? label : best);
   result[q.name] = {score:a.score, level, confidence, probabilities:distribution};
  }
 }
 return result;
}
export function route(answer: any, type: string, labels: string[], yesAt: number, noAt: number): {branch: string; index: number} {
 if (!Number.isFinite(yesAt) || !Number.isFinite(noAt) || noAt < 0 || yesAt > 1 || noAt >= yesAt) throw new Error('Thresholds must satisfy 0 ≤ No at < Yes at ≤ 1');
 const branch = type === 'predicate' ? (answer.probability >= yesAt ? 'yes' : answer.probability <= noAt ? 'no' : 'unsure') : type === 'choice' ? answer.choice : answer.level;
 const index = labels.indexOf(branch);
 if (index < 0) throw new Error('Answer does not match a configured output');
 return {branch, index};
}
export function imageMime(bytes: Uint8Array): string {
 if (bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff) return 'image/jpeg';
 if ([137,80,78,71,13,10,26,10].every((v,i) => bytes[i] === v)) return 'image/png';
 if (Buffer.from(bytes.slice(0,4)).toString() === 'RIFF' && Buffer.from(bytes.slice(8,12)).toString() === 'WEBP') return 'image/webp';
 throw new Error('Image must be PNG, JPEG or WebP');
}
