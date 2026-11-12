const { document, window } = globalThis;
const screen = document.querySelector('#screen');
const feedback = document.querySelector('#feedback');
const scenarioControl = document.querySelector('#scenario');
const parameters = new window.URLSearchParams(window.location.search);
const scenarios = [
  'trois',
  'deux',
  'une',
  'reserve',
  'images',
  'long',
  'vide',
  'erreur',
];
const state = {
  view: parameters.get('vue') === 'comparaison' ? 'comparaison' : 'atelier',
  scenario: scenarios.includes(parameters.get('donnees'))
    ? parameters.get('donnees')
    : 'trois',
  selectedId: null,
  exploredId: null,
  brief: null,
};
let baseResponse;
let returnFocus;
let ready = false;

const icons = {
  leaf: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M19 4C8 2 3 8 6 14c4 7 14 3 13-10Z"/><path d="M4 21 16 8M10 15v-5m0 5h5"/></svg>',
  warning:
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m12 3 10 18H2L12 3Z"/><path d="M12 9v5m0 3v1"/></svg>',
  brief:
    '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M8 4H5v17h14V4h-3M8 3h8v4H8zM8 11h8M8 15h6"/></svg>',
  check:
    '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>',
};

function escape(value) {
  return String(value ?? '').replace(
    /[&<>"']/g,
    (character) =>
      ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
      })[character],
  );
}

function announce(message) {
  feedback.textContent = message;
}

function initialBrief() {
  return {
    application: baseResponse.compris?.type_produit || 'Produit à préciser',
    volume: '',
    constraints: (baseResponse.compris?.contraintes || []).join(', '),
  };
}

function propositions() {
  const pistes = window.structuredClone(baseResponse.pistes || []);
  if (state.scenario === 'vide' || state.scenario === 'erreur') return [];
  if (state.scenario === 'une') return pistes.slice(0, 1);
  if (state.scenario === 'deux') return pistes.slice(0, 2);
  if (state.scenario === 'reserve') {
    for (const piste of pistes) {
      piste.references_sans_label = [
        { arome: 'citron vert', code: 'DEMO-003', label_manquant: 'bio' },
      ];
    }
  }
  if (state.scenario === 'long') {
    pistes[0].nom =
      'Citron vert, notes de zeste et expression fraîche pour une boisson pétillante';
    pistes[0].explication = `${pistes[0].explication} Ce texte supplémentaire sert à vérifier la lisibilité de la maquette avec une explication longue. Il ne correspond pas à une nouvelle recommandation du service Data.`;
    pistes[0].references[0].profil_sensoriel +=
      ', texte de démonstration volontairement long pour vérifier le retour à la ligne et la lisibilité sur petit écran';
  }
  return pistes;
}

function imageFor(arome, className = 'thumbnail') {
  const images = { 'citron vert': 'lime.webp', citron: 'lemon.webp' };
  const filename = state.scenario === 'images' ? null : images[arome];
  if (!filename)
    return `<span class="${className} ingredient-fallback" role="img" aria-label="${escape(arome)} : illustration indisponible">${icons.leaf}</span>`;
  return `<img class="${className}" src="./assets/${filename}" alt="${escape(arome)}, illustration" width="184" height="184" />`;
}

function compactAssociation(piste) {
  const aromes = piste.aromes || [];
  if (aromes.length < 2) return imageFor(aromes[0]);
  return `<span class="thumbnail compact-pair" role="img" aria-label="Association : ${escape(aromes.join(' et '))}">${aromes
    .slice(0, 2)
    .map((arome) => imageFor(arome, 'association-thumb'))
    .join('')}</span>`;
}

function association(piste) {
  const aromes = piste.aromes || [];
  return `<div class="ingredient-association ${aromes.length > 1 ? 'is-pair' : ''}">
    ${aromes
      .slice(0, 2)
      .map((arome) => imageFor(arome, 'ingredient'))
      .join('')}
    ${aromes.length > 1 ? '<span class="association-sign" aria-hidden="true">+</span>' : ''}
  </div>`;
}

function reservations(piste) {
  const missing = (piste.sans_reference || []).map(
    (arome) =>
      `${arome} : aucune référence disponible. Création sur mesure à étudier avec un expert.`,
  );
  const labels = (piste.references_sans_label || []).map(
    (reference) =>
      `${reference.label_manquant} : label non renseigné pour ${reference.arome} (${reference.code}). À vérifier avec un expert.`,
  );
  return [...missing, ...labels];
}

function warnings(piste) {
  return reservations(piste)
    .map(
      (text) =>
        `<p class="reserve">${icons.warning}<span>${escape(text)}</span></p>`,
    )
    .join('');
}

function profiles(piste, chips = false) {
  const references = piste.references || [];
  if (!references.length) return '<p>Profil sensoriel non fourni.</p>';
  return references
    .map((reference) =>
      chips
        ? `<p><strong>${escape(reference.nom)}</strong></p><ul class="sensory-line">${(
            reference.profil_sensoriel || 'Profil non fourni'
          )
            .split(',')
            .map((note) => `<li>${escape(note.trim())}</li>`)
            .join('')}</ul>`
        : `<p><strong>${escape(reference.nom)}</strong><br />${escape(reference.profil_sensoriel || 'Profil non fourni')}</p>`,
    )
    .join('');
}

function technicalDetails(piste) {
  return `<details class="reference-details"><summary>Références et détails techniques</summary>
    ${(piste.references || []).map((reference) => `<div class="reference-entry"><strong>${escape(reference.code)} · ${escape(reference.nom)}</strong><p>Forme : ${escape(reference.forme || 'non renseignée')}</p><p>Labels de la référence fictive : ${escape((reference.labels || []).join(', ') || 'non renseignés')}</p></div>`).join('') || '<p>Aucune référence disponible.</p>'}
    <p class="local-note">Références DEMO fictives, à valider avec un expert.</p>
  </details>`;
}

function chooseButton(piste) {
  const selected = piste.id === state.selectedId;
  return `<div class="choice-actions"><button type="button" class="primary-button" data-action="choose" data-id="${escape(piste.id)}" aria-pressed="${selected}" aria-label="${selected ? 'Piste choisie' : 'Choisir la piste'} : ${escape(piste.nom)}">${selected ? `${icons.check} Piste choisie` : 'Choisir cette piste'}</button>${selected ? '<button type="button" class="quiet-button inline-review" data-action="review">Vérifier mon brief</button>' : ''}</div>`;
}

function briefData() {
  return `<dl class="brief-data"><div><dt>Votre produit</dt><dd>${escape(state.brief.application)}</dd></div><div><dt>Contraintes de recette</dt><dd>${escape(state.brief.constraints || 'À préciser')}</dd></div><div><dt>Volume envisagé</dt><dd>${escape(state.brief.volume || 'À préciser')}</dd></div></dl>`;
}

function briefPanel(pistes) {
  const selected = pistes.find((piste) => piste.id === state.selectedId);
  return `<aside class="brief-panel" aria-labelledby="brief-title"><h2 id="brief-title">${icons.brief} Votre brief</h2>
    ${briefData()}
    <div class="selection-slot ${selected ? 'has-choice' : ''}">
      ${
        selected
          ? `<span class="choice-heading">${icons.check} Piste ajoutée au brief</span><strong>${escape(selected.nom)}</strong><small>${escape((selected.aromes || []).join(' + '))}</small>${warnings(selected)}`
          : '<span class="field-label">Votre direction de goût</span><p>Choisissez une piste pour compléter votre brief.</p>'
      }
    </div>
    <button class="primary-button" type="button" data-action="review" ${selected ? '' : 'disabled'}>Vérifier mon brief</button>
    <p class="brief-next">Puis un engagement de <strong>10 € fictifs</strong>, avant de préparer la demande.</p>
  </aside>`;
}

function atelier(pistes) {
  const current =
    pistes.find((piste) => piste.id === state.exploredId) || pistes[0];
  return `<div class="workbench"><section class="discovery" aria-label="Explorer les pistes">
    <div class="shortlist" style="--count: ${pistes.length}">${pistes.map((piste) => `<button class="explore" type="button" data-action="explore" data-id="${escape(piste.id)}" aria-pressed="${piste.id === current.id}" aria-label="Explorer : ${escape(piste.nom)}">${compactAssociation(piste)}<span><strong>${escape(piste.nom)}</strong><small>${reservations(piste).length ? 'Point à vérifier' : escape(piste.description)}</small></span></button>`).join('')}</div>
    <article class="tasting-sheet" aria-labelledby="piste-title"><div class="tasting-top">${association(current)}<div><p class="composition-label">${escape(current.description)}</p><h2 id="piste-title">${escape(current.nom)}</h2><p class="piste-reason">${escape(current.explication)}</p></div></div>
      <div class="sensory-section"><span class="field-label">Profil sensoriel des références disponibles</span>${profiles(current, true)}</div>
      <div class="sheet-body">${warnings(current)}<div class="sheet-action"><span>Ce choix reste modifiable.</span>${chooseButton(current)}</div>${technicalDetails(current)}</div>
    </article>
    ${assistantNote()}
    <p class="commercial-note">Votre choix prépare une dégustation à discuter avec un expert. Le commercial vérifiera le projet avant toute commande.</p>
  </section>${briefPanel(pistes)}</div>`;
}

function comparaison(pistes) {
  return `<div class="workbench"><section class="discovery" aria-label="Comparer les pistes"><p class="count-caption">${pistes.length} ${pistes.length > 1 ? 'pistes proposées' : 'piste proposée'} pour votre projet</p>
    <div class="comparison-list">${pistes.map((piste) => `<article class="comparison-row" data-selected="${piste.id === state.selectedId}">${compactAssociation(piste)}<div><p class="comparison-description">${escape(piste.description)}</p><h2>${escape(piste.nom)}</h2><div class="comparison-info"><div><span class="field-label">Profil sensoriel</span>${profiles(piste)}</div><div><span class="field-label">Pourquoi cette piste ?</span><p>${escape(piste.explication)}</p></div></div>${warnings(piste)}<div class="row-actions">${technicalDetails(piste)}${chooseButton(piste)}</div></div></article>`).join('')}</div>
    ${assistantNote()}<p class="commercial-note">Votre sélection constitue un brief. Elle sera revue avec un commercial avant toute commande.</p>
  </section>${briefPanel(pistes)}</div>`;
}

function assistantNote() {
  return `<details class="assistant-note"><summary>Lire le conseil de l’assistant IA</summary><p>${escape(baseResponse.reponse)}</p></details>`;
}

function emptyState() {
  const failed = state.scenario === 'erreur';
  return `<section class="empty-state" aria-label="${failed ? 'Erreur de chargement' : 'Aucune proposition'}"><h2>${failed ? 'Les pistes ne sont pas disponibles.' : 'Votre projet demande une précision.'}</h2><p>${failed ? 'Votre brief est conservé. Vous pouvez réessayer pour retrouver les propositions.' : 'Aucune piste n’est proposée pour ce scénario. Vérifiez votre projet avant de poursuivre.'}</p><button class="primary-button" type="button" data-action="${failed ? 'retry' : 'edit'}">${failed ? 'Réessayer' : 'Préciser mon projet'}</button>${failed ? '' : '<button class="quiet-button" type="button" data-action="help">Comment choisir ?</button>'}</section>`;
}

function updateUrl() {
  const url = new window.URL(window.location.href);
  url.searchParams.set('vue', state.view);
  url.searchParams.set('donnees', state.scenario);
  window.history.replaceState(null, '', url);
}

function render(focusSelector) {
  const pistes = propositions();
  screen.className = state.view;
  screen.innerHTML = `<div class="screen-heading"><div><h1>Choisissez votre direction de goût.</h1><p>Pour votre ${escape(state.brief.application)}, ${pistes.length > 1 ? 'comparez les profils et choisissez une piste pour votre brief.' : 'découvrez la proposition et vérifiez qu’elle correspond à votre idée.'}</p></div><button type="button" class="project-link" data-action="edit">${icons.brief} Modifier mon projet</button></div>${pistes.length ? (state.view === 'atelier' ? atelier(pistes) : comparaison(pistes)) : emptyState()}`;
  for (const link of document.querySelectorAll('[data-view]')) {
    const active = link.dataset.view === state.view;
    if (active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
    link.href = `?vue=${link.dataset.view}&donnees=${state.scenario}`;
  }
  scenarioControl.value = state.scenario;
  updateUrl();
  if (focusSelector) document.querySelector(focusSelector)?.focus();
}

function openDialog(id, trigger) {
  returnFocus = trigger;
  document.querySelector(`#${id}`).showModal();
}

function openEditor(trigger) {
  document.querySelector('#application').value = state.brief.application;
  document.querySelector('#volume').value = state.brief.volume;
  document.querySelector('#constraints').value = state.brief.constraints;
  openDialog('editor', trigger);
  document.querySelector('#application').focus();
}

function openReview(trigger) {
  const piste = propositions().find((item) => item.id === state.selectedId);
  if (!piste) return;
  document.querySelector('#review-content').innerHTML =
    `${briefData()}<div class="review-choice"><span class="field-label">Votre direction de goût</span><h3>${escape(piste.nom)}</h3>${profiles(piste)}${warnings(piste)}</div>`;
  openDialog('review', trigger);
}

document.addEventListener('click', (event) => {
  if (!ready) return;
  const viewLink = event.target.closest('[data-view]');
  if (
    viewLink &&
    !event.ctrlKey &&
    !event.metaKey &&
    !event.shiftKey &&
    event.button === 0
  ) {
    event.preventDefault();
    state.view = viewLink.dataset.view;
    render();
    announce(
      `Présentation ${state.view === 'atelier' ? 'Atelier' : 'Comparaison'}. Votre sélection est conservée.`,
    );
    return;
  }
  const closeButton = event.target.closest('[data-close]');
  if (closeButton) {
    document.querySelector(`#${closeButton.dataset.close}`).close();
    return;
  }
  const button = event.target.closest('button[data-action]');
  if (!button) return;
  const { action, id } = button.dataset;
  if (action === 'explore') {
    state.exploredId = id;
    render();
    const current = [
      ...document.querySelectorAll('[data-action="explore"]'),
    ].find((item) => item.dataset.id === id);
    current?.focus();
    announce(
      `Piste explorée : ${propositions().find((item) => item.id === id)?.nom}.`,
    );
  } else if (action === 'choose') {
    state.selectedId = id;
    render();
    const selected = [
      ...document.querySelectorAll('[data-action="choose"]'),
    ].find((item) => item.dataset.id === id);
    selected?.focus();
    announce(
      `${propositions().find((item) => item.id === id)?.nom} ajouté à votre brief. Vous pouvez vérifier votre brief.`,
    );
  } else if (action === 'edit') openEditor(button);
  else if (action === 'review') openReview(button);
  else if (action === 'help') openDialog('help', button);
  else if (action === 'retry') {
    state.scenario = 'trois';
    state.exploredId = null;
    state.selectedId = null;
    render('[data-action="edit"]');
    announce('Les propositions sont à nouveau disponibles.');
  }
});

scenarioControl.addEventListener('change', () => {
  state.scenario = scenarioControl.value;
  state.selectedId = null;
  state.exploredId = null;
  state.brief = initialBrief();
  if (state.scenario === 'reserve') state.brief.constraints += ', bio';
  render();
  announce('Scénario changé. La sélection est réinitialisée.');
});

document.querySelector('#brief-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const fields = new window.FormData(event.target);
  const application = String(fields.get('application') || '').trim();
  if (!application) {
    const input = document.querySelector('#application');
    input.setCustomValidity('Précisez le produit que vous préparez.');
    input.reportValidity();
    return;
  }
  const nextBrief = {
    application,
    volume: String(fields.get('volume') || '').trim(),
    constraints: String(fields.get('constraints') || '').trim(),
  };
  const changed = JSON.stringify(nextBrief) !== JSON.stringify(state.brief);
  state.brief = nextBrief;
  if (changed) state.selectedId = null;
  document.querySelector('#editor').close();
  render('[data-action="edit"]');
  announce(
    changed
      ? 'Brief modifié. Choisissez de nouveau une piste avant de vérifier votre brief.'
      : 'Votre brief est conservé.',
  );
});

document
  .querySelector('#application')
  .addEventListener('input', (event) => event.target.setCustomValidity(''));

for (const dialog of document.querySelectorAll('dialog')) {
  dialog.addEventListener('close', () => {
    if (returnFocus?.isConnected) returnFocus.focus();
    else document.querySelector('[data-action="edit"]')?.focus();
  });
  dialog.addEventListener('click', (event) => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (
      event.clientX < bounds.left ||
      event.clientX > bounds.right ||
      event.clientY < bounds.top ||
      event.clientY > bounds.bottom
    )
      dialog.close();
  });
}

document.addEventListener(
  'error',
  (event) => {
    const image = event.target;
    if (image.tagName !== 'IMG' || !image.closest('#screen')) return;
    const placeholder = document.createElement('span');
    placeholder.className = `${image.className} ingredient-fallback`;
    placeholder.setAttribute('role', 'img');
    placeholder.setAttribute(
      'aria-label',
      `${image.alt} : illustration indisponible`,
    );
    placeholder.innerHTML = icons.leaf;
    image.replaceWith(placeholder);
  },
  true,
);

try {
  const response = await window.fetch('./pistes.json');
  if (!response.ok) throw new Error('Fixture unavailable');
  baseResponse = await response.json();
  if (!Array.isArray(baseResponse.pistes)) throw new Error('Invalid fixture');
  state.brief = initialBrief();
  if (state.scenario === 'reserve') state.brief.constraints += ', bio';
  document.querySelector('#attribution').textContent =
    `Source du scénario : ${baseResponse.attribution || 'données de démonstration'}.`;
  ready = true;
  render();
} catch {
  ready = false;
  screen.innerHTML =
    '<section class="empty-state"><h1>La maquette ne peut pas charger ses données.</h1><p>Servez ce dossier avec le serveur Vite ou un serveur HTTP local, puis rechargez la page.</p></section>';
  scenarioControl.disabled = true;
  for (const control of document.querySelectorAll(
    '[data-action], [data-view]',
  )) {
    if (control.tagName === 'BUTTON') control.disabled = true;
  }
}
