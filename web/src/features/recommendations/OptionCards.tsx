import { ArrowRight, Check, Leaf } from 'lucide-react';
import { Button } from '../../components/ui/Button.tsx';
import type {
  ConversationSnapshot,
  FlavorOption,
} from '../../services/conversation-service.ts';
import { IngredientImage, resolveIngredient } from './IngredientImage.tsx';

export function OptionCards({
  snapshot,
  pending,
  onSelect,
  onReject,
  onExpert,
}: {
  snapshot: ConversationSnapshot;
  pending: boolean;
  onSelect: (piste: FlavorOption) => void;
  onReject: () => void;
  onExpert: () => void;
}) {
  return (
    <section className="options-section" aria-labelledby="options-title">
      <div className="options-heading">
        <div>
          <span className="eyebrow">À votre goût</span>
          <h2 id="options-title">Trois pistes, à vous d’explorer.</h2>
        </div>
        <span className="demo-label">Références de démonstration</span>
      </div>
      <div className="options-grid">
        {snapshot.pistes
          .toSorted((a, b) => a.rang - b.rang)
          .map((piste) => (
            <article className="option-card" key={piste.id}>
              <div className="option-image">
                <IngredientImage
                  ingredient={resolveIngredient(
                    piste.id,
                    piste.references.map((ref) => ref.code),
                  )}
                  decorative
                />
                <span className="option-position">0{piste.rang}</span>
              </div>
              <div className="option-content">
                <span className="option-category">
                  <Leaf size={12} aria-hidden="true" /> {piste.description}
                </span>
                <h3>{piste.nom}</h3>
                <p className="option-explanation">{piste.explication}</p>
                <div className="option-profile">
                  {piste.references[0]?.profil_sensoriel ??
                    'Un profil à préciser avec un expert.'}
                </div>
                <div className="option-codes">
                  {piste.references.map((ref) => ref.code).join(' / ') ||
                    'Sans référence proche'}
                </div>
                <Button
                  variant={piste.rang === 1 ? 'primary' : 'secondary'}
                  disabled={pending}
                  onClick={() => onSelect(piste)}
                >
                  Choisir cet arôme <ArrowRight size={16} aria-hidden="true" />
                </Button>
              </div>
            </article>
          ))}
      </div>
      <div className="options-bottom">
        <span>
          <Check size={14} aria-hidden="true" /> Le choix vous appartient, vous
          pouvez encore affiner.
        </span>
        <button className="text-button" disabled={pending} onClick={onReject}>
          Aucun ne me convient
        </button>
      </div>
      <p className="attribution">
        {snapshot.attribution} Les références DEMO sont fictives.
      </p>
      <button className="text-button expert-inline" onClick={onExpert}>
        Vous préférez en parler avec un expert ?{' '}
        <ArrowRight size={14} aria-hidden="true" />
      </button>
    </section>
  );
}
