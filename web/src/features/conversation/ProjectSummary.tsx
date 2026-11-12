import { Check, ChevronDown, Leaf, PencilLine, Sparkles } from 'lucide-react';
import type { ConversationSnapshot } from '../../services/conversation-service.ts';

export function ProjectSummary({
  snapshot,
  onEdit,
}: {
  snapshot: ConversationSnapshot | null;
  onEdit: () => void;
}) {
  const understood = snapshot?.compris;
  const selected = snapshot?.pistes.find(
    (piste) => piste.id === snapshot.brief?.piste_id,
  );
  return (
    <aside className="project-summary">
      <details open>
        <summary>
          <span>
            <Leaf size={18} strokeWidth={1.5} aria-hidden="true" /> Votre idée
            prend forme
          </span>
          <ChevronDown size={17} aria-hidden="true" />
        </summary>
        <div className="summary-body">
          <p className="summary-intro">
            Ce que nous avons compris, au fil de nos échanges.
          </p>
          <dl>
            <div>
              <dt>Votre produit</dt>
              <dd>{understood?.type_produit ?? 'À préciser ensemble'}</dd>
            </div>
            <div>
              <dt>Le goût recherché</dt>
              <dd>
                {understood?.aromes.length
                  ? understood.aromes.join(', ')
                  : 'À imaginer'}
              </dd>
            </div>
            <div>
              <dt>Ce qui compte pour vous</dt>
              <dd>
                {understood?.contraintes.length ? (
                  <div className="constraint-tags">
                    {understood.contraintes.map((item) => (
                      <span key={item}>
                        <Check size={11} aria-hidden="true" />
                        {item}
                      </span>
                    ))}
                  </div>
                ) : (
                  'Aucune préférence précisée'
                )}
              </dd>
            </div>
          </dl>
          {selected ? (
            <div className="summary-selection">
              <span>
                <Check size={14} aria-hidden="true" /> Votre sélection
              </span>
              <strong>{selected.nom}</strong>
              <small>
                {selected.references.map((ref) => ref.code).join(' · ')}
              </small>
            </div>
          ) : null}
          <button className="text-button summary-edit" onClick={onEdit}>
            <PencilLine size={14} aria-hidden="true" /> Préciser mon projet
          </button>
          <div className="summary-foot">
            <Sparkles size={16} strokeWidth={1.4} aria-hidden="true" />
            <p>
              Votre idée reste le fil conducteur.
              <br />
              Le choix final se construit avec vous.
            </p>
          </div>
        </div>
      </details>
    </aside>
  );
}
