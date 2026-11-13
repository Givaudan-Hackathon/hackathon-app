import { useEffect, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CircleHelp,
  Leaf,
  MessageCircle,
  RotateCcw,
} from 'lucide-react';
import { Brand } from '../components/ui/Brand.tsx';
import { Button } from '../components/ui/Button.tsx';
import { Dialog } from '../components/ui/Dialog.tsx';
import { JourneyNavigation } from '../components/ui/JourneyNavigation.tsx';
import { useConversation } from '../features/conversation/useConversation.ts';
import { ConversationPanel } from '../features/conversation/ConversationPanel.tsx';
import { IdeaEditor } from '../features/conversation/IdeaEditor.tsx';
import { ProjectSummary } from '../features/conversation/ProjectSummary.tsx';
import { OptionCards } from '../features/recommendations/OptionCards.tsx';
import { BriefReview } from '../features/request/BriefReview.tsx';
import { RequestForm } from '../features/request/RequestForm.tsx';
import { Confirmation } from '../features/request/Confirmation.tsx';
import { PaymentPanel } from '../features/payment/PaymentPanel.tsx';
import { createConversationRuntime } from '../services/conversation-runtime.ts';
import { createMockRequestService } from '../services/adapters/mock-request.ts';
import { createMockPaymentService } from '../services/adapters/mock-payment.ts';
import {
  emptyContact,
  type RequestReceipt,
} from '../services/request-service.ts';
import {
  briefKey,
  paymentMatchesBrief,
  type PaymentReceipt,
} from '../services/payment-service.ts';
import type { FlavorOption } from '../services/conversation-service.ts';
import { buildJourney, type JourneyPage } from './journey.ts';
import { Home } from './Home.tsx';

type View = 'home' | JourneyPage | 'done';
export function App() {
  const [runtime] = useState(() => createConversationRuntime());
  const [services] = useState(() => ({
    conversation: runtime.service,
    request: createMockRequestService(),
    payment: createMockPaymentService(),
  }));
  const { state, send, reset, cancel, retry } = useConversation(
    services.conversation,
  );
  const [view, setView] = useState<View>('home');
  const [dialog, setDialog] = useState<
    'help' | 'reset' | 'privacy' | 'brief' | null
  >(null);
  const [kind, setKind] = useState<'sample' | 'expert'>('sample');
  const [receipt, setReceipt] = useState<RequestReceipt | null>(null);
  const [payment, setPayment] = useState<PaymentReceipt | null>(null);
  const [contact, setContact] = useState(() => ({ ...emptyContact }));
  const [checkoutPending, setCheckoutPending] = useState(false);
  const [idea, setIdea] = useState('');
  const [committedIdea, setCommittedIdea] = useState('');
  const [conversationDraft, setConversationDraft] = useState('');
  const snapshot = state.snapshot;
  const validPayment = paymentMatchesBrief(payment, snapshot?.brief ?? null)
    ? payment
    : null;
  const pending = state.pending || checkoutPending;
  const hasProject = state.messages.length > 0;
  const current: JourneyPage =
    view === 'home' ? 'idea' : view === 'done' ? 'request' : view;
  const steps = buildJourney({
    hasProject,
    hasOptions: Boolean(snapshot?.pistes.length),
    hasBrief: Boolean(snapshot?.brief),
    hasPayment: Boolean(validPayment),
    expert: kind === 'expert',
    finished: Boolean(receipt),
  });
  const step = steps.findIndex((entry) => entry.id === current);
  useEffect(() => {
    document.title =
      view === 'home'
        ? 'Givaudan — Le goût de vos idées'
        : view === 'done'
          ? 'Demande simulée — Givaudan'
          : `Étape ${step + 1} sur 5 : ${steps[step].label} — Givaudan`;
    if (view !== 'home')
      document
        .querySelector<HTMLElement>('main h1')
        ?.focus({ preventScroll: true });
  }, [view, step]);
  useEffect(() => {
    if (!hasProject || receipt) return;
    const guard = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    window.addEventListener('beforeunload', guard);
    return () => window.removeEventListener('beforeunload', guard);
  }, [hasProject, receipt]);
  function changeView(next: View) {
    setView(next);
    window.scrollTo({ top: 0, behavior: 'instant' });
  }
  function startFresh() {
    reset();
    setReceipt(null);
    setPayment(null);
    setContact({ ...emptyContact });
    setKind('sample');
    setDialog(null);
    setIdea('');
    setCommittedIdea('');
    setConversationDraft('');
    setCheckoutPending(false);
    changeView('home');
  }
  function home() {
    if (pending) return;
    if (hasProject && !receipt) setDialog('reset');
    else startFresh();
  }
  function edit() {
    if (pending) return;
    changeView('refine');
    requestAnimationFrame(() =>
      document
        .querySelector<HTMLTextAreaElement>('.chat-composer textarea')
        ?.focus(),
    );
  }
  function showSnapshot(result: NonNullable<typeof snapshot>) {
    if (!paymentMatchesBrief(payment, result.brief)) setPayment(null);
    if (snapshot && snapshot.session_id !== result.session_id)
      setCommittedIdea('');
    changeView(result.pistes.length ? 'choose' : 'refine');
  }
  async function sendText(message: string) {
    const result = await send(message);
    if (!result) return false;
    showSnapshot(result);
    return true;
  }
  async function retryConversation() {
    const result = await retry();
    if (result) showSnapshot(result);
  }
  function start(message: string) {
    setIdea(message);
    setCommittedIdea(message);
    setKind('sample');
    changeView('refine');
    setConversationDraft(message);
    void sendText(message).then((success) => {
      if (success) setConversationDraft('');
    });
  }
  async function choose(piste: FlavorOption) {
    if (pending) return;
    const result = await send('', piste.id, `Je choisis ${piste.nom}.`);
    if (!result) return;
    setKind('sample');
    if (!paymentMatchesBrief(payment, result.brief)) setPayment(null);
    changeView('choose');
    requestAnimationFrame(() =>
      document
        .querySelector<HTMLButtonElement>('.inline-brief-review')
        ?.focus({ preventScroll: true }),
    );
  }
  function expert() {
    if (pending) return;
    setKind('expert');
    changeView('request');
  }
  async function beginCheckout(reviewPayment = false) {
    if (pending || !snapshot?.brief) return;
    setKind('sample');
    setDialog(null);
    if (snapshot.echantillons) {
      changeView(reviewPayment || !validPayment ? 'payment' : 'request');
      return;
    }
    const result = await send('Je souhaite préparer ma demande d’échantillon.');
    if (!result) return;
    if (!paymentMatchesBrief(payment, result.brief)) setPayment(null);
    if (result.brief && result.echantillons)
      changeView(
        paymentMatchesBrief(payment, result.brief) && !reviewPayment
          ? 'request'
          : 'payment',
      );
    else showSnapshot(result);
  }
  function navigate(page: JourneyPage) {
    if (
      pending ||
      receipt ||
      !steps.find((entry) => entry.id === page)?.available
    )
      return;
    if (page === 'idea' && view === 'home') {
      document
        .querySelector<HTMLTextAreaElement>('.idea-form textarea')
        ?.focus();
      return;
    }
    if (page === 'payment') {
      beginCheckout(true);
      return;
    }
    if (page === 'choose') setKind('sample');
    changeView(page);
  }
  function continueIdea() {
    const text = idea.trim();
    if (!text || pending) return;
    if (text === committedIdea && snapshot)
      changeView(snapshot.pistes.length ? 'choose' : 'refine');
    else {
      setCommittedIdea(text);
      changeView('refine');
      setConversationDraft(text);
      void sendText(text).then((success) => {
        if (success) setConversationDraft('');
      });
    }
  }
  function paid(next: PaymentReceipt) {
    if (!paymentMatchesBrief(next, snapshot?.brief ?? null)) return;
    setPayment(next);
    changeView('request');
  }
  function complete(next: RequestReceipt) {
    setReceipt(next);
    changeView('done');
  }
  const projectDescription = state.messages
    .filter((message) => message.role === 'user')
    .map((message) => message.text)
    .join(' / ');
  const conversation = (
    <ConversationPanel
      state={state}
      onSend={sendText}
      draft={conversationDraft}
      onDraftChange={setConversationDraft}
      compact={view === 'choose'}
      mode={runtime.mode}
    />
  );
  const isWorkspace = view === 'idea' || view === 'refine' || view === 'choose';
  return (
    <div className="app">
      <a className="skip-link" href="#main">
        Aller au contenu
      </a>
      <header className="site-header">
        <div className="page-shell header-inner">
          <Brand onClick={home} />
          {view === 'home' ? (
            <nav className="desktop-nav" aria-label="Navigation principale">
              <a href="#nos-aromes">Les arômes à explorer</a>
              <a href="#comment-ca-marche">Comment ça marche</a>
            </nav>
          ) : (
            <span className="header-project-label">
              Créons le goût de votre prochaine idée.
            </span>
          )}
          <button
            className="help-button"
            aria-label="Obtenir de l’aide"
            onClick={() => setDialog('help')}
          >
            <CircleHelp size={17} strokeWidth={1.5} aria-hidden="true" />
            <span>Un coup de main ?</span>
          </button>
        </div>
      </header>
      <div className="demo-banner">
        <span className="demo-dot" /> Démonstration interactive{' '}
        <span className="demo-banner-detail">
          {runtime.mode === 'http'
            ? '— assistant IA · paiement et envoi simulés'
            : '— échanges, paiements et demandes simulés'}
        </span>
      </div>
      {view !== 'home' ? (
        <JourneyNavigation
          steps={steps}
          current={current}
          pending={pending}
          finished={Boolean(receipt)}
          onNavigate={navigate}
        />
      ) : null}
      <main id="main">
        {view === 'home' ? <Home onStart={start} /> : null}
        {isWorkspace ? (
          <div className={`workspace page-shell workspace-${view}`}>
            <div className="workspace-top">
              <button className="text-button" onClick={home} disabled={pending}>
                <ArrowLeft size={15} aria-hidden="true" /> Nouvelle idée
              </button>
              <span>Votre projet, à votre rythme</span>
            </div>
            <div className="workspace-title">
              <div>
                <h1 tabIndex={-1}>
                  {view === 'idea'
                    ? 'Tout commence par votre idée.'
                    : view === 'choose'
                      ? 'Choisissez votre direction de goût.'
                      : 'Précisons votre projet.'}
                </h1>
              </div>
            </div>
            {state.error ? (
              <div className="conversation-error" role="alert">
                <p>{state.error}</p>
                <div>
                  <button
                    className="text-button"
                    disabled={pending}
                    onClick={() => void retryConversation()}
                  >
                    Réessayer
                  </button>
                  <button
                    className="text-button"
                    disabled={pending}
                    onClick={edit}
                  >
                    Préciser mon projet
                  </button>
                </div>
              </div>
            ) : null}
            {state.notice ? (
              <p className="notice" role="status">
                {state.notice}
              </p>
            ) : null}
            {state.pending ? (
              <div className="conversation-progress" role="status">
                <span>L’assistant analyse votre projet…</span>
                <button className="text-button" onClick={cancel}>
                  Annuler l’attente
                </button>
              </div>
            ) : null}
            {view === 'idea' ? (
              <IdeaEditor
                value={idea}
                pending={pending}
                onChange={setIdea}
                onContinue={continueIdea}
              />
            ) : (
              <div
                className={
                  view === 'choose' ? 'atelier-layout' : 'workspace-grid'
                }
              >
                <div className="workspace-content">
                  {view === 'choose' && snapshot?.pistes.length ? (
                    <OptionCards
                      snapshot={snapshot}
                      pending={pending}
                      onSelect={(piste) => void choose(piste)}
                      onReject={() =>
                        void sendText('Aucun de ces arômes ne me convient.')
                      }
                      onExpert={expert}
                      onReview={() => setDialog('brief')}
                    />
                  ) : null}
                  {view === 'choose' ? (
                    <details
                      className="conversation-drawer"
                      open={Boolean(state.error)}
                    >
                      <summary>
                        <MessageCircle size={18} aria-hidden="true" /> Retrouver
                        la conversation ou préciser mon idée
                      </summary>
                      {conversation}
                    </details>
                  ) : (
                    conversation
                  )}
                  {view === 'refine' ? (
                    <div className="clarification-questions">
                      {snapshot?.questions.map((question) => (
                        <fieldset key={question.id}>
                          <legend
                            className={
                              question.question.trim() ===
                              snapshot.reponse.trim()
                                ? 'sr-only'
                                : undefined
                            }
                          >
                            {question.question}
                          </legend>
                          <div className="quick-answers">
                            {question.choix.map((choice) => (
                              <button
                                key={choice}
                                disabled={pending}
                                onClick={() => void sendText(choice)}
                              >
                                {choice}
                              </button>
                            ))}
                          </div>
                        </fieldset>
                      ))}
                      <button
                        className="text-button"
                        disabled={pending}
                        onClick={expert}
                      >
                        En parler avec un expert
                      </button>
                    </div>
                  ) : null}
                </div>
                <ProjectSummary
                  snapshot={snapshot}
                  onEdit={edit}
                  pending={pending}
                  onReview={
                    view === 'choose' ? () => setDialog('brief') : undefined
                  }
                />
              </div>
            )}
          </div>
        ) : null}
        {view === 'payment' && snapshot?.brief ? (
          <div className="page-shell checkout-page">
            <PaymentPanel
              key={briefKey(snapshot.brief)}
              snapshot={snapshot}
              service={services.payment}
              receipt={validPayment}
              onComplete={paid}
              onBack={() => changeView('choose')}
              onExpert={expert}
              onPendingChange={setCheckoutPending}
            />
          </div>
        ) : null}
        {view === 'request' && (kind === 'expert' || validPayment) ? (
          <div className="page-shell request-page">
            <div className="workspace-top">
              <button
                className="text-button"
                disabled={pending}
                onClick={() =>
                  changeView(
                    kind === 'expert'
                      ? snapshot?.pistes.length
                        ? 'choose'
                        : 'refine'
                      : 'payment',
                  )
                }
              >
                <ArrowLeft size={15} aria-hidden="true" />{' '}
                {kind === 'expert' ? 'Mon projet' : 'Revoir le paiement fictif'}
              </button>
              <span>Relisez votre demande avant de confirmer.</span>
            </div>
            <h1 className="sr-only" tabIndex={-1}>
              Préparer votre demande
            </h1>
            <RequestForm
              key={`${kind}-${briefKey(snapshot?.brief ?? null)}`}
              service={services.request}
              brief={snapshot?.brief ?? null}
              projectDescription={projectDescription}
              kind={kind}
              onComplete={complete}
              onBack={() =>
                changeView(snapshot?.pistes.length ? 'choose' : 'refine')
              }
              values={contact}
              onValuesChange={setContact}
              payment={validPayment}
              onPendingChange={setCheckoutPending}
            />
          </div>
        ) : null}
        {view === 'done' && receipt ? (
          <div className="page-shell">
            <Confirmation receipt={receipt} onRestart={startFresh} />
          </div>
        ) : null}
      </main>
      <footer className="site-footer">
        <div className="page-shell footer-inner">
          <span>
            <Leaf size={15} strokeWidth={1.4} aria-hidden="true" />{' '}
            L’inspiration est dans la nature. Le projet est le vôtre.
          </span>
          <div>
            <button onClick={() => setDialog('privacy')}>Vos données</button>
            <a
              href="https://www.givaudan.com/taste-wellbeing"
              target="_blank"
              rel="noreferrer"
            >
              Découvrir Givaudan <ArrowRight size={13} aria-hidden="true" />
            </a>
          </div>
          <span className="footer-copyright">Givaudan · Prototype 2026</span>
        </div>
      </footer>
      <Dialog
        open={dialog === 'brief'}
        onClose={() => setDialog(null)}
        title="Vérifier votre brief"
      >
        {snapshot?.brief ? (
          <BriefReview
            snapshot={snapshot}
            pending={pending}
            onContinue={() => void beginCheckout()}
            onEdit={() => {
              setDialog(null);
              edit();
            }}
            paid={Boolean(validPayment)}
          />
        ) : null}
      </Dialog>
      <Dialog
        open={dialog === 'help'}
        onClose={() => setDialog(null)}
        title="Votre projet, pas à pas"
      >
        <p>
          Décrivez votre produit et le goût que vous imaginez. L’assistant vous
          aide à préciser votre besoin et à explorer des arômes.
        </p>
        <ol className="help-steps">
          <li>Décrivez votre idée avec vos mots.</li>
          <li>Affinez le goût et vos préférences.</li>
          <li>Comparez et choisissez une proposition.</li>
          <li>
            Simulez un paiement d’engagement pour une demande d’échantillon.
          </li>
          <li>
            Relisez votre projet, complétez vos coordonnées et confirmez la
            demande simulée.
          </li>
        </ol>
        <p>Vous pouvez aussi demander l’avis d’un expert sans paiement.</p>
        <div className="notice">
          {runtime.mode === 'http'
            ? 'La conversation utilise le service IA. Les références DEMO, le paiement et le dépôt restent illustratifs.'
            : 'Ce prototype utilise des réponses et références fictives.'}{' '}
          Aucun débit réel ni envoi au commercial.
        </div>
        <Button onClick={() => setDialog(null)}>
          J’ai compris <Check size={16} aria-hidden="true" />
        </Button>
      </Dialog>
      <Dialog
        open={dialog === 'privacy'}
        onClose={() => setDialog(null)}
        title="Vos données dans cette démonstration"
      >
        <p>
          {runtime.mode === 'http'
            ? 'Les messages décrivant votre projet sont transmis à notre service IA pour préciser le besoin. Vos coordonnées restent dans cette page et ne sont pas envoyées au commercial.'
            : 'Votre description et vos coordonnées restent dans la mémoire de cette page. Aucun message n’est envoyé à une IA ou à un commercial.'}
        </p>
        <p>
          Le paiement est entièrement fictif. Aucune donnée bancaire n’est
          collectée. Recharger ou quitter la page réinitialise la démonstration.
        </p>
        <Button onClick={() => setDialog(null)}>Fermer</Button>
      </Dialog>
      <Dialog
        open={dialog === 'reset'}
        onClose={() => setDialog(null)}
        title="Explorer une nouvelle idée ?"
      >
        <p>
          Le projet en cours, les coordonnées saisies et le paiement fictif
          seront réinitialisés. Vous pourrez démarrer une nouvelle conversation.
        </p>
        <div className="dialog-actions">
          <Button variant="secondary" onClick={() => setDialog(null)}>
            Garder mon projet
          </Button>
          <Button onClick={startFresh}>
            <RotateCcw size={16} aria-hidden="true" /> Nouvelle idée
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
