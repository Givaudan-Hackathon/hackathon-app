import { useEffect, useId, useRef, useState, type FormEvent } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CreditCard,
  Leaf,
  LockKeyhole,
  ShieldCheck,
} from 'lucide-react';
import { Button } from '../../components/ui/Button.tsx';
import type { ConversationSnapshot } from '../../services/conversation-service.ts';
import {
  briefKey,
  formatDemoAmount,
  type PaymentReceipt,
  type PaymentService,
} from '../../services/payment-service.ts';
import {
  IngredientImage,
  resolveIngredient,
} from '../recommendations/IngredientImage.tsx';

export function PaymentPanel({
  snapshot,
  service,
  receipt,
  onComplete,
  onBack,
  onExpert,
  onPendingChange,
}: {
  snapshot: ConversationSnapshot;
  service: PaymentService;
  receipt: PaymentReceipt | null;
  onComplete: (receipt: PaymentReceipt) => void;
  onBack: () => void;
  onExpert: () => void;
  onPendingChange: (pending: boolean) => void;
}) {
  const id = useId();
  const [accepted, setAccepted] = useState(false);
  const [outcome, setOutcome] = useState<'success' | 'declined'>('success');
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const busy = useRef(false);
  const controller = useRef<AbortController | null>(null);
  const key = useRef(crypto.randomUUID());
  const checkbox = useRef<HTMLInputElement>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const selected = snapshot.pistes.find(
    (piste) => piste.id === snapshot.brief?.piste_id,
  );
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy.current) return;
    if (!accepted) {
      setError('Confirmez votre intérêt pour ce projet avant de continuer.');
      checkbox.current?.focus();
      return;
    }
    busy.current = true;
    setPending(true);
    onPendingChange(true);
    setError(null);
    const current = new AbortController();
    controller.current = current;
    try {
      const result = await service.pay(
        {
          idempotencyKey: key.current,
          briefKey: briefKey(snapshot.brief),
          outcome,
        },
        { signal: current.signal },
      );
      if (!current.signal.aborted) onComplete(result);
    } catch (err) {
      if (!current.signal.aborted)
        setError(
          err instanceof Error
            ? err.message
            : 'La simulation a échoué. Réessayez.',
        );
    } finally {
      busy.current = false;
      onPendingChange(false);
      if (!current.signal.aborted) setPending(false);
    }
  }
  return (
    <section className="payment-layout" aria-labelledby="payment-title">
      <div className="payment-story">
        <span className="eyebrow">
          <Leaf size={16} aria-hidden="true" /> Une idée qui mérite d’aller plus
          loin
        </span>
        <h1 id="payment-title" tabIndex={-1}>
          Donnons une suite
          <br />à votre projet.
        </h1>
        <p>
          Cette étape représente votre engagement avant la préparation d’une
          demande d’échantillon. Un expert examinera ensuite votre besoin.
        </p>
        {selected ? (
          <div className="payment-project">
            <IngredientImage
              ingredient={resolveIngredient(
                selected.id,
                selected.references.map((ref) => ref.code),
              )}
              decorative
            />
            <div>
              <small>Votre projet</small>
              <strong>{selected.nom}</strong>
              <span>{snapshot.brief?.type_produit}</span>
              <span>
                {snapshot.brief?.contraintes.join(' · ') ||
                  'Préférences à préciser'}
              </span>
            </div>
          </div>
        ) : null}
        <div className="payment-purpose">
          <ShieldCheck size={22} aria-hidden="true" />
          <p>
            Le paiement illustre une intention de poursuivre. La faisabilité et
            les conditions de votre projet restent à confirmer avec un expert.
          </p>
        </div>
        <button className="text-button" disabled={pending} onClick={onBack}>
          <ArrowLeft size={16} aria-hidden="true" /> Revoir mon choix
        </button>
      </div>
      <div className="payment-card">
        <div className="payment-card-heading">
          <span>
            <CreditCard size={19} aria-hidden="true" /> Paiement fictif
          </span>
          <span className="demo-label">Démonstration</span>
        </div>
        <div className="payment-price">
          <span>Engagement pour votre projet</span>
          <strong>{formatDemoAmount()}</strong>
          <small>Montant illustratif, à valider pour le service final.</small>
        </div>
        <div
          className="payment-demo-card"
          aria-label="Moyen de paiement de démonstration"
        >
          <CreditCard size={26} aria-hidden="true" />
          <span>Carte de démonstration</span>
          <strong>•••• &nbsp; •••• &nbsp; •••• &nbsp; 4242</strong>
          <small>Aucune donnée bancaire à renseigner</small>
        </div>
        {receipt ? (
          <div className="payment-already">
            <p role="status">
              <Check size={18} aria-hidden="true" /> Paiement déjà simulé pour
              ce projet.
            </p>
            <Button onClick={() => onComplete(receipt)}>
              Continuer vers ma demande{' '}
              <ArrowRight size={16} aria-hidden="true" />
            </Button>
          </div>
        ) : (
          <form
            onSubmit={(event) => void submit(event)}
            noValidate
            aria-busy={pending}
          >
            <label className="payment-consent" htmlFor={`${id}-consent`}>
              <input
                ref={checkbox}
                id={`${id}-consent`}
                type="checkbox"
                checked={accepted}
                disabled={pending}
                onChange={(event) => {
                  setAccepted(event.target.checked);
                  setError(null);
                }}
                aria-describedby={error ? `${id}-error` : `${id}-notice`}
              />
              <span>
                Je confirme mon intérêt pour ce projet et souhaite préparer ma
                demande d’échantillon.
              </span>
            </label>
            <details className="payment-scenarios">
              <summary>Tester un scénario de démonstration</summary>
              <label htmlFor={`${id}-scenario`}>
                Résultat du paiement fictif
              </label>
              <select
                id={`${id}-scenario`}
                value={outcome}
                disabled={pending}
                onChange={(event) => {
                  setOutcome(event.target.value as 'success' | 'declined');
                  setError(null);
                }}
              >
                <option value="success">Paiement accepté</option>
                <option value="declined">Paiement refusé</option>
              </select>
            </details>
            {error ? (
              <p className="error-notice" id={`${id}-error`} role="alert">
                {error}
              </p>
            ) : null}
            <Button type="submit" loading={pending} className="payment-submit">
              Simuler le paiement de {formatDemoAmount()}{' '}
              <ArrowRight size={16} aria-hidden="true" />
            </Button>
          </form>
        )}
        <p className="payment-disclaimer" id={`${id}-notice`}>
          <LockKeyhole size={16} aria-hidden="true" />
          <span>
            Aucun débit réel. Aucune carte bancaire collectée. Ce paiement
            fictif ne déclenche ni commande ni envoi.
          </span>
        </p>
        <button
          className="text-button payment-expert"
          disabled={pending}
          onClick={onExpert}
        >
          Je préfère contacter un expert sans paiement
        </button>
      </div>
    </section>
  );
}
