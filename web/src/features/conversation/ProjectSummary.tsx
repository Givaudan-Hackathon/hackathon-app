import { Check, ClipboardList, PencilLine } from 'lucide-react';
import type { ConversationSnapshot } from '../../services/conversation-service.ts';
import { Button } from '../../components/ui/Button.tsx';
import { FlavorWarnings } from '../recommendations/FlavorWarnings.tsx';

export function ProjectSummary({
  snapshot,
  onEdit,
  onReview,
  pending = false,
}: {
  snapshot: ConversationSnapshot | null;
  onEdit: () => void;
  onReview?: () => void;
  pending?: boolean;
}) {
  const understood = snapshot?.compris;
  const selected = snapshot?.pistes.find(
    (piste) => piste.id === snapshot.brief?.piste_id,
  );
  const volume =
    snapshot?.brief?.volume ??
    (typeof understood?.volume === 'string' ? understood.volume : null);
  return (
    <aside
      className="project-summary atelier-sidebar"
      aria-labelledby="project-title"
    >
      <h2 id="project-title" tabIndex={-1}>
        <ClipboardList size={20} aria-hidden="true" />
        {onReview ? 'Votre brief' : 'Votre projet'}
      </h2>
      <dl>
        <div>
          <dt>Votre produit</dt>
          <dd>{understood?.type_produit || 'À préciser'}</dd>
        </div>
        <div>
          <dt>Le goût recherché</dt>
          <dd>{understood?.aromes.join(', ') || 'À préciser'}</dd>
        </div>
        {understood?.profil.length ? (
          <div>
            <dt>Profil recherché</dt>
            <dd>{understood.profil.join(', ')}</dd>
          </div>
        ) : null}
        <div>
          <dt>Contraintes de recette</dt>
          <dd>{understood?.contraintes.join(', ') || 'À préciser'}</dd>
        </div>
        <div>
          <dt>Volume envisagé</dt>
          <dd>{volume || 'À préciser'}</dd>
        </div>
      </dl>
      {onReview ? (
        <>
          <div className={`atelier-brief-slot ${selected ? 'has-choice' : ''}`}>
            {selected ? (
              <>
                <span>
                  <Check size={14} aria-hidden="true" /> Piste ajoutée au brief
                </span>
                <strong>{selected.nom}</strong>
                <FlavorWarnings
                  missing={snapshot?.brief?.creation_sur_mesure}
                  labels={snapshot?.brief?.references_sans_label}
                />
              </>
            ) : (
              <p>Choisissez une piste pour compléter votre brief.</p>
            )}
          </div>
          <Button onClick={onReview} disabled={pending || !selected}>
            Vérifier mon brief
          </Button>
          <p className="atelier-next">
            Puis un engagement de <strong>10 € fictifs</strong>, avant de
            préparer la demande.
          </p>
        </>
      ) : null}
      <button
        className="text-button summary-edit"
        disabled={pending}
        onClick={onEdit}
      >
        <PencilLine size={14} aria-hidden="true" /> Préciser mon projet
      </button>
    </aside>
  );
}
