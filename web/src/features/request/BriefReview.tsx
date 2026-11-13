import { ArrowRight, Check, PencilLine } from 'lucide-react';
import type { ConversationSnapshot } from '../../services/conversation-service.ts';
import { Button } from '../../components/ui/Button.tsx';
import { FlavorWarnings } from '../recommendations/FlavorWarnings.tsx';
import {
  IngredientImage,
  resolveIngredient,
} from '../recommendations/IngredientImage.tsx';

export function BriefReview({
  snapshot,
  pending,
  onContinue,
  onEdit,
  paid = false,
}: {
  snapshot: ConversationSnapshot;
  pending: boolean;
  onContinue: () => void;
  onEdit: () => void;
  paid?: boolean;
}) {
  const selected = snapshot.pistes.find(
    (piste) => piste.id === snapshot.brief?.piste_id,
  );
  if (!selected || !snapshot.brief) return null;
  return (
    <section className="brief-review" aria-labelledby="brief-title">
      <div className="review-photo">
        <IngredientImage
          ingredient={resolveIngredient(
            selected.id,
            selected.references.map((ref) => ref.code),
          )}
          decorative
        />
      </div>
      <div className="review-content">
        <span className="eyebrow">
          <Check size={14} aria-hidden="true" /> Votre choix
        </span>
        <h2 id="brief-title" tabIndex={-1}>
          {selected.nom}
        </h2>
        <p>{selected.references[0]?.profil_sensoriel}</p>
        <FlavorWarnings
          missing={snapshot.brief.creation_sur_mesure}
          labels={snapshot.brief.references_sans_label}
        />
        <dl>
          <div>
            <dt>Profil recherché</dt>
            <dd>{snapshot.brief.profil.join(', ') || 'À préciser'}</dd>
          </div>
          <div>
            <dt>Volume envisagé</dt>
            <dd>{snapshot.brief.volume || 'À préciser'}</dd>
          </div>
          <div>
            <dt>Pour votre</dt>
            <dd>{snapshot.brief.type_produit}</dd>
          </div>
          <div>
            <dt>Vos préférences</dt>
            <dd>
              {snapshot.brief.contraintes.join(', ') ||
                'À préciser avec votre conseiller'}
            </dd>
          </div>
        </dl>
        <span className="demo-label">
          Références fictives {snapshot.brief.codes_references.join(' / ')}
        </span>
        <div className="review-actions">
          <Button loading={pending} onClick={onContinue}>
            {paid ? 'Compléter ma demande' : 'Passer au paiement fictif'}{' '}
            <ArrowRight size={17} aria-hidden="true" />
          </Button>
          <button className="text-button" disabled={pending} onClick={onEdit}>
            <PencilLine size={14} aria-hidden="true" /> Ajuster mon idée
          </button>
        </div>
        <small>
          Un paiement fictif précède la demande. Aucun débit ni envoi réel dans
          cette démonstration.
        </small>
      </div>
    </section>
  );
}
