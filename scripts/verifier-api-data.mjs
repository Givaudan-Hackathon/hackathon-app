import assert from 'node:assert/strict';
import console from 'node:console';
import { performance } from 'node:perf_hooks';
import process from 'node:process';
import { URL } from 'node:url';

const baseUrl = (process.argv[2] ?? 'http://127.0.0.1:8000').replace(
  /\/+$/,
  '',
);
const results = [];

async function request(path, options = {}) {
  const start = performance.now();
  const response = await globalThis.fetch(`${baseUrl}${path}`, {
    ...options,
    signal: globalThis.AbortSignal.timeout(10_000),
  });
  assert.equal(response.status, 200, `${path} : HTTP ${response.status}`);
  const body = await response.json();
  results.push({
    route: path,
    status: response.status,
    milliseconds: Math.round(performance.now() - start),
  });
  return body;
}

try {
  const health = await request('/sante');
  assert.equal(health.statut, 'ok');
  assert.equal(typeof health.version_modele, 'string');

  for (const brief of [
    'arôme fraise pour yaourt à boire',
    'sirop goût menthe pour cafés',
    'boisson protéinée goût vanille',
  ]) {
    const body = await request('/recommander', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brief, k: 2 }),
    });
    assert.equal(body.brief, brief);
    assert.ok(['flavors', 'fragrance', 'indeterminee'].includes(body.division));
    assert.equal(typeof body.version_modele, 'string');
    assert.equal(typeof body.attribution, 'string');
    assert.ok(body.attribution.length > 0);
    assert.ok(Array.isArray(body.recommandations));
    assert.equal(body.recommandations.length, 2);
    for (const product of body.recommandations) {
      assert.equal(typeof product.code, 'string');
      assert.equal(typeof product.categorie, 'string');
      assert.equal(typeof product.score, 'number');
      assert.ok(product.score >= 0 && product.score <= 1);
      assert.ok(
        ['http:', 'https:'].includes(new URL(product.url_produit).protocol),
      );
    }
  }
  console.log(JSON.stringify({ baseUrl, results, success: true }, null, 2));
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
}
