import { useEffect, useId, useRef, useState, type FormEvent } from 'react';
import { ArrowRight, Check, LockKeyhole, Mail } from 'lucide-react';
import { Button } from '../../components/ui/Button.tsx';
import {
  contactSchema,
  type RequestInput,
  type RequestReceipt,
  type RequestService,
  type ContactDraft,
} from '../../services/request-service.ts';
import type { ClientBrief } from '../../services/conversation-service.ts';
import {
  formatDemoAmount,
  type PaymentReceipt,
} from '../../services/payment-service.ts';

type Props = {
  service: RequestService;
  brief: ClientBrief | null;
  projectDescription: string;
  kind: 'sample' | 'expert';
  onComplete: (receipt: RequestReceipt) => void;
  onBack: () => void;
  values: ContactDraft;
  onValuesChange: (values: ContactDraft) => void;
  payment: PaymentReceipt | null;
  onPendingChange: (pending: boolean) => void;
};
export function RequestForm({
  service,
  brief,
  projectDescription,
  kind,
  onComplete,
  onBack,
  values,
  onValuesChange,
  payment,
  onPendingChange,
}: Props) {
  const id = useId();
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const busy = useRef(false);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const key = useRef(crypto.randomUUID());
  const formRef = useRef<HTMLFormElement>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy.current) return;
    const parsed = contactSchema.safeParse(values);
    if (!parsed.success) {
      const next: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        const field = String(issue.path[0]);
        if (!next[field]) next[field] = issue.message;
      }
      setErrors(next);
      formRef.current
        ?.querySelector<HTMLElement>(`[name="${Object.keys(next)[0]}"]`)
        ?.focus();
      return;
    }
    setErrors({});
    setError(null);
    setPending(true);
    busy.current = true;
    onPendingChange(true);
    const input: RequestInput = {
      idempotencyKey: key.current,
      kind,
      contact: parsed.data,
      brief,
      projectDescription,
      payment,
    };
    const current = new AbortController();
    controller.current = current;
    try {
      const receipt = await service.submit(input, { signal: current.signal });
      if (!current.signal.aborted) onComplete(receipt);
    } catch (err) {
      if (current.signal.aborted) return;
      setError(
        err instanceof Error
          ? err.message
          : 'La demande n’a pas pu être simulée. Réessayez.',
      );
    } finally {
      busy.current = false;
      onPendingChange(false);
      if (!current.signal.aborted) setPending(false);
    }
  }
  function change(name: keyof typeof values, value: string) {
    onValuesChange({ ...values, [name]: value });
    setErrors((current) => ({ ...current, [name]: '' }));
  }
  const field = (
    name: 'name' | 'company' | 'email' | 'phone',
    label: string,
    type: string,
    autocomplete: string,
    placeholder: string,
  ) => (
    <div className="form-field">
      <label htmlFor={`${id}-${name}`}>{label}</label>
      <input
        id={`${id}-${name}`}
        name={name}
        type={type}
        required={name !== 'phone'}
        autoComplete={autocomplete}
        value={values[name]}
        onChange={(event) => change(name, event.target.value)}
        placeholder={placeholder}
        spellCheck={name !== 'email'}
        aria-invalid={Boolean(errors[name])}
        aria-describedby={errors[name] ? `${id}-${name}-error` : undefined}
        disabled={pending}
        maxLength={name === 'phone' ? 30 : name === 'email' ? 254 : 160}
      />
      {errors[name] ? (
        <span className="field-error" id={`${id}-${name}-error`}>
          {errors[name]}
        </span>
      ) : null}
    </div>
  );
  return (
    <section className="request-section" aria-labelledby="request-title">
      <div className="request-intro">
        <span className="eyebrow">
          <Mail size={15} aria-hidden="true" /> La suite se construit ensemble
        </span>
        <h2 id="request-title">
          Parlons de
          <br />
          votre projet.
        </h2>
        <p>
          {kind === 'sample'
            ? 'Une dernière étape pour préparer votre demande d’échantillon.'
            : 'Préparez une demande de contact pour préciser votre besoin avec un expert.'}
        </p>
        <div className="request-steps">
          <span>
            <Check size={16} aria-hidden="true" /> Un expert examinera votre
            besoin
          </span>
          <span>
            <Check size={16} aria-hidden="true" /> Les conditions seront
            confirmées avec vous
          </span>
          <span>
            <Check size={16} aria-hidden="true" /> Votre demande reste soumise à
            validation
          </span>
        </div>
        <div className="request-demo">
          <LockKeyhole size={19} aria-hidden="true" />
          <p>
            Vous explorez une démonstration.
            <br />
            Aucune coordonnée ne sera transmise.
          </p>
        </div>
        {kind === 'sample' && payment ? (
          <div className="request-payment-status">
            <Check size={18} aria-hidden="true" />
            <div>
              <strong>
                Paiement fictif validé : {formatDemoAmount(payment.amountCents)}
              </strong>
              <span>
                Aucun débit réel. Relisez votre demande avant de confirmer.
              </span>
            </div>
          </div>
        ) : null}
        <button className="text-button" onClick={onBack} disabled={pending}>
          Revenir à mon projet
        </button>
      </div>
      <form
        ref={formRef}
        onSubmit={(event) => void submit(event)}
        noValidate
        className="request-form"
        aria-busy={pending}
      >
        <div className="form-group-title">Votre projet</div>
        <div className="form-grid">
          <div className="form-field">
            <label htmlFor={`${id}-stage`}>Où en êtes-vous ?</label>
            <select
              id={`${id}-stage`}
              name="projectStage"
              required
              value={values.projectStage}
              onChange={(event) => change('projectStage', event.target.value)}
              disabled={pending}
              aria-invalid={Boolean(errors.projectStage)}
              aria-describedby={
                errors.projectStage ? `${id}-stage-error` : undefined
              }
            >
              <option value="">Choisissez une étape…</option>
              <option value="exploration">J’explore une idée</option>
              <option value="prototype">Je développe un prototype</option>
              <option value="launch">Je prépare un lancement</option>
            </select>
            {errors.projectStage ? (
              <span className="field-error" id={`${id}-stage-error`}>
                {errors.projectStage}
              </span>
            ) : null}
          </div>
          <div className="form-field">
            <label htmlFor={`${id}-volume`}>Produit fini prévu par mois</label>
            <select
              id={`${id}-volume`}
              name="monthlyVolume"
              required
              value={values.monthlyVolume}
              onChange={(event) => change('monthlyVolume', event.target.value)}
              disabled={pending}
              aria-invalid={Boolean(errors.monthlyVolume)}
              aria-describedby={
                errors.monthlyVolume ? `${id}-volume-error` : undefined
              }
            >
              <option value="">Choisissez une quantité…</option>
              <option value="under_500">Moins de 500 kg</option>
              <option value="500_5000">De 500 kg à 5 tonnes</option>
              <option value="over_5000">Plus de 5 tonnes</option>
              <option value="unknown">Je ne sais pas encore</option>
            </select>
            {errors.monthlyVolume ? (
              <span className="field-error" id={`${id}-volume-error`}>
                {errors.monthlyVolume}
              </span>
            ) : null}
          </div>
        </div>
        <div className="form-group-title">Vos coordonnées</div>
        <div className="form-grid">
          {field('name', 'Prénom et nom', 'text', 'name', 'Camille Martin…')}
          {field(
            'company',
            'Société',
            'text',
            'organization',
            'Votre société…',
          )}
          {field(
            'email',
            'E-mail professionnel',
            'email',
            'email',
            'camille@exemple.fr…',
          )}
          {field('phone', 'Téléphone (facultatif)', 'tel', 'tel', '+33…')}
        </div>
        {error ? (
          <div className="error-notice" role="alert">
            {error}
          </div>
        ) : null}
        {Object.values(errors).some(Boolean) ? (
          <p className="sr-only" role="alert">
            Vérifiez les champs indiqués pour continuer.
          </p>
        ) : null}
        <Button type="submit" loading={pending} className="request-submit">
          Simuler l’envoi de ma demande{' '}
          <ArrowRight size={17} aria-hidden="true" />
        </Button>
        <p className="form-footnote">
          Vos informations restent dans cette page. Elles ne sont ni envoyées à
          un commercial, ni enregistrées en base.
        </p>
      </form>
    </section>
  );
}
