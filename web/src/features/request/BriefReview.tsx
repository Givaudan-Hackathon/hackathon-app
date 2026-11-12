import { ArrowRight, Check, PencilLine } from 'lucide-react';
import type { ConversationSnapshot } from '../../services/conversation-service.ts';
import { Button } from '../../components/ui/Button.tsx';
import {
  IngredientImage,
  resolveIngredient,
} from '../recommendations/IngredientImage.tsx';

export function BriefReview({
  snapshot,
  pending,
  onContinue,
  onEdit,
}: {
  snapshot: ConversationSnapshot;
  pending: boolean;
  onContinue: () => void;
  onEdit: () => void;
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
        <h2 id="brief-title">{selected.nom}</h2>
        <p>{selected.references[0]?.profil_sensoriel}</p>
        <dl>
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
            Préparer ma demande <ArrowRight size={17} aria-hidden="true" />
          </Button>
          <button className="text-button" disabled={pending} onClick={onEdit}>
            <PencilLine size={14} aria-hidden="true" /> Ajuster mon idée
          </button>
        </div>
        <small>
          Une demande sans engagement. Un expert examinera ensuite votre projet.
        </small>
      </div>
    </section>
  );
}
