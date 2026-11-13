import { useState } from 'react';
import { Check, Leaf } from 'lucide-react';
import { Button } from '../../components/ui/Button.tsx';
import type {
  ConversationSnapshot,
  FlavorOption,
} from '../../services/conversation-service.ts';
import { IngredientImage, resolveIngredient } from './IngredientImage.tsx';
import { FlavorWarnings } from './FlavorWarnings.tsx';

function Association({
  piste,
  compact = false,
}: {
  piste: FlavorOption;
  compact?: boolean;
}) {
  if (piste.image && !compact)
    return (
      <div className="atelier-association">
        <IngredientImage
          ingredient={null}
          source={piste.image}
          label={piste.nom}
          decorative
          eager
        />
      </div>
    );
  const aromes = piste.aromes.slice(0, 2);
  return (
    <div
      className={`atelier-association ${compact ? 'is-thumbnail' : ''} ${aromes.length > 1 ? 'is-pair' : ''}`}
      aria-hidden="true"
    >
      {aromes.map((arome, index) => (
        <IngredientImage
          key={`${arome}-${index}`}
          ingredient={resolveIngredient(arome, [])}
          decorative
          eager
        />
      ))}
      {aromes.length > 1 && !compact ? (
        <span className="association-plus">+</span>
      ) : null}
    </div>
  );
}

export function OptionCards({
  snapshot,
  pending,
  onSelect,
  onReject,
  onExpert,
  onReview,
}: {
  snapshot: ConversationSnapshot;
  pending: boolean;
  onSelect: (piste: FlavorOption) => void;
  onReject: () => void;
  onExpert: () => void;
  onReview: () => void;
}) {
  const [exploredId, setExploredId] = useState<string | null>(null);
  const pistes = snapshot.pistes.toSorted((a, b) => a.rang - b.rang);
  const active =
    pistes.find(
      (piste) => piste.id === (exploredId ?? snapshot.brief?.piste_id),
    ) ?? pistes[0];
  if (!active) return null;
  const selected = snapshot.brief?.piste_id === active.id;
  return (
    <section
      className="options-section atelier-options"
      aria-labelledby="options-title"
      aria-busy={pending}
    >
      <div className="options-heading">
        <h2 id="options-title">
          {pistes.length} {pistes.length > 1 ? 'pistes' : 'piste'} pour votre
          projet
        </h2>
        <span className="demo-label">Références DEMO fictives</span>
      </div>
      <div
        className="atelier-alternatives"
        role="group"
        aria-label="Explorer les pistes"
      >
        {pistes.map((piste) => (
          <button
            type="button"
            className="atelier-option"
            key={piste.id}
            disabled={pending}
            aria-pressed={active.id === piste.id}
            aria-controls="piste-detail"
            aria-label={`Explorer : ${piste.nom}`}
            onClick={() => setExploredId(piste.id)}
          >
            <Association piste={piste} compact />
            <span>
              <strong>{piste.nom}</strong>
              <small>
                {snapshot.brief?.piste_id === piste.id
                  ? 'Ajoutée au brief'
                  : piste.sans_reference.length ||
                      piste.references_sans_label.length
                    ? 'Point à vérifier'
                    : piste.description}
              </small>
            </span>
          </button>
        ))}
      </div>
      <article
        id="piste-detail"
        className="atelier-sheet"
        aria-labelledby="piste-title"
      >
        <div className="atelier-sheet-top">
          <Association piste={active} />
          <div>
            <p className="atelier-kind">{active.description}</p>
            <h3 id="piste-title">{active.nom}</h3>
            <p className="atelier-reason">{active.explication}</p>
          </div>
        </div>
        <div className="atelier-profiles">
          <span className="atelier-field">
            Profil sensoriel des références disponibles
          </span>
          {active.references.length ? (
            active.references.map((reference) => (
              <div key={reference.code}>
                <strong>{reference.nom}</strong>
                <ul>
                  {reference.profil_sensoriel
                    .split(',')
                    .filter(Boolean)
                    .map((note, index) => (
                      <li key={`${note}-${index}`}>{note.trim()}</li>
                    ))}
                </ul>
              </div>
            ))
          ) : (
            <p>Le profil sera précisé avec un expert.</p>
          )}
        </div>
        <div className="atelier-sheet-bottom">
          <FlavorWarnings
            missing={active.sans_reference}
            labels={active.references_sans_label}
          />
          <div className="atelier-selection">
            <span>Votre choix reste modifiable.</span>
            <div>
              <Button
                disabled={pending || selected}
                loading={pending}
                onClick={() => onSelect(active)}
                aria-pressed={selected}
              >
                {selected ? (
                  <>
                    <Check size={16} aria-hidden="true" /> Piste ajoutée
                  </>
                ) : (
                  'Choisir cette piste'
                )}
              </Button>
              {selected ? (
                <Button
                  variant="secondary"
                  disabled={pending}
                  onClick={onReview}
                  className="inline-brief-review"
                >
                  Vérifier mon brief
                </Button>
              ) : null}
            </div>
          </div>
          <details className="atelier-references">
            <summary>Références et détails techniques</summary>
            {active.references.map((reference) => (
              <div key={reference.code}>
                <strong>
                  {reference.code} · {reference.nom}
                </strong>
                <p>Forme : {reference.forme}</p>
                <p>
                  Labels de la référence fictive :{' '}
                  {reference.labels.join(', ') || 'non renseignés'}
                </p>
              </div>
            ))}
          </details>
        </div>
      </article>
      <div className="atelier-options-footer">
        <button className="text-button" disabled={pending} onClick={onReject}>
          Aucune de ces pistes ne me convient
        </button>
        <button className="text-button" disabled={pending} onClick={onExpert}>
          En parler avec un expert
        </button>
      </div>
      <p className="attribution">
        <Leaf size={13} aria-hidden="true" /> {snapshot.attribution}
      </p>
    </section>
  );
}
