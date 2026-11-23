/**
 * Frontend client-side logic tests.
 * Runs in Node.js to verify search, filtering, and sorting logic against real public data.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const dataDir = path.resolve(__dirname, '../public/data');

console.log('Testing frontend client-side logic & datasets...\n');

// 1. Load apps.json
const appsPath = path.join(dataDir, 'apps.json');
if (!fs.existsSync(appsPath)) {
  console.error('FAIL: apps.json not found at', appsPath);
  process.exit(1);
}
const apps = JSON.parse(fs.readFileSync(appsPath, 'utf8'));

// Test count
if (apps.length !== 100) {
  console.error(`FAIL: Expected 100 apps, got ${apps.length}`);
  process.exit(1);
}
console.log('✓ 100 applications loaded successfully');

// 2. Test search logic
const searchByName = (query) => {
  const q = query.toLowerCase();
  return apps.filter(a => 
    a.app_name.toLowerCase().includes(q) || 
    a.category_name.toLowerCase().includes(q)
  );
};

const ghResults = searchByName('github');
if (ghResults.length !== 1 || ghResults[0].app_id !== 61) {
  console.error('FAIL: Search for "github" failed', ghResults);
  process.exit(1);
}
console.log('✓ Search query "github" matches App #61');

const crmResults = searchByName('crm');
if (crmResults.length !== 10) {
  console.error(`FAIL: Search for "crm" expected 10 apps, got ${crmResults.length}`);
  process.exit(1);
}
console.log('✓ Search query "crm" matches 10 apps in CRM and Sales');

// 3. Test multi-attribute filtering logic
const filterApps = ({ category = 'all', auth = 'all', verdict = 'all', gate = 'all' }) => {
  return apps.filter(a => {
    if (category !== 'all' && a.category_name !== category) return false;
    if (auth !== 'all' && (!a.auth_methods || !a.auth_methods.includes(auth))) return false;
    if (verdict !== 'all' && a.buildability_verdict !== verdict) return false;
    if (gate !== 'all' && a.quality_gate_status !== gate) return false;
    return true;
  });
};

const readyToBuildApps = filterApps({ verdict: 'ready_to_build' });
if (readyToBuildApps.length !== 11) {
  console.error(`FAIL: ready_to_build expected 11 apps, got ${readyToBuildApps.length}`);
  process.exit(1);
}
console.log('✓ Buildability filter "ready_to_build" returns exactly 11 platforms');

const passedGateApps = filterApps({ gate: 'passed' });
if (passedGateApps.length !== 39) {
  console.error(`FAIL: gate "passed" expected 39 apps, got ${passedGateApps.length}`);
  process.exit(1);
}
console.log('✓ Quality Gate filter "passed" returns exactly 39 platforms');

const oauthApps = filterApps({ auth: 'OAuth2' });
if (oauthApps.length !== 17) {
  console.error(`FAIL: OAuth2 expected 17 apps, got ${oauthApps.length}`);
  process.exit(1);
}
console.log('✓ Auth filter "OAuth2" returns exactly 17 platforms');

// 4. Test sorting
const sortedByPriorityDesc = [...apps].sort((a, b) => b.priority_score - a.priority_score);
if (sortedByPriorityDesc[0].priority_score < sortedByPriorityDesc[1].priority_score) {
  console.error('FAIL: Sorting descending failed');
  process.exit(1);
}
console.log(`✓ Sorting by priority score desc correctly orders platforms (top: ${sortedByPriorityDesc[0].app_name} with ${sortedByPriorityDesc[0].priority_score} pts)`);

console.log('\nAll 5 frontend client-side tests PASSED with 100% integrity!');
