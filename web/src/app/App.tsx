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
import { createMockConversationService } from '../services/adapters/mock-conversation.ts';
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
  const [services] = useState(() => ({
    conversation: createMockConversationService(),
    request: createMockRequestService(),
    payment: createMockPaymentService(),
  }));
  const { state, send, reset } = useConversation(services.conversation);
  const [view, setView] = useState<View>('home');
  const [dialog, setDialog] = useState<'help' | 'reset' | 'privacy' | null>(
    null,
  );
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
  async function sendText(message: string) {
    const result = await send(message);
    if (!result) return false;
    if (!paymentMatchesBrief(payment, result.brief)) setPayment(null);
    if (result.etape === 'echantillons') {
      setKind('sample');
      changeView(
        paymentMatchesBrief(payment, result.brief) ? 'request' : 'payment',
      );
    } else changeView(result.etape === 'relance' ? 'refine' : 'choose');
    return true;
  }
  function start(message: string) {
    setIdea(message);
    setCommittedIdea(message);
    setKind('sample');
    changeView('refine');
    void sendText(message);
  }
  async function choose(piste: FlavorOption) {
    if (pending) return;
    const result = await send('', piste.id, `Je choisis ${piste.nom}.`);
    if (!result) return;
    setKind('sample');
    if (!paymentMatchesBrief(payment, result.brief)) setPayment(null);
    changeView('choose');
    requestAnimationFrame(() =>
      document.getElementById('brief-title')?.focus(),
    );
  }
  function expert() {
    if (pending) return;
    setKind('expert');
    changeView('request');
  }
  function beginCheckout(reviewPayment = false) {
    if (pending || !snapshot?.brief) return;
    setKind('sample');
    if (snapshot.echantillons)
      changeView(reviewPayment || !validPayment ? 'payment' : 'request');
    else void sendText('Je souhaite préparer ma demande d’échantillon.');
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
      void sendText(text);
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
          — échanges, paiements et demandes simulés
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
                <span className="eyebrow">Créons les bonnes connexions</span>
                <h1 tabIndex={-1}>
                  {view === 'idea'
                    ? 'Tout commence par votre idée.'
                    : view === 'choose'
                      ? 'Les possibilités prennent goût.'
                      : 'Faisons grandir votre idée.'}
                </h1>
              </div>
            </div>
            {view === 'idea' ? (
              <IdeaEditor
                value={idea}
                pending={pending}
                onChange={setIdea}
                onContinue={continueIdea}
              />
            ) : (
              <div
                className={`workspace-grid ${view === 'choose' ? 'is-choosing' : ''}`}
              >
                {view === 'choose' ? (
                  <ProjectSummary snapshot={snapshot} onEdit={edit} compact />
                ) : null}
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
                    />
                  ) : null}
                  {view === 'choose' && snapshot?.brief ? (
                    <BriefReview
                      snapshot={snapshot}
                      pending={pending}
                      onContinue={() => beginCheckout()}
                      onEdit={edit}
                      paid={Boolean(validPayment)}
                    />
                  ) : null}
                  {view === 'choose' ? (
                    <details className="conversation-drawer">
                      <summary>
                        <MessageCircle size={18} aria-hidden="true" /> Retrouver
                        la conversation ou préciser mon idée
                      </summary>
                      {conversation}
                    </details>
                  ) : (
                    conversation
                  )}
                  {view === 'refine' && !state.pending ? (
                    <div className="quick-answers">
                      <span>Pour vous aider :</span>
                      {(!snapshot?.compris.type_produit
                        ? ['Une boisson pétillante', 'Un dessert végétal']
                        : !snapshot.compris.arome
                          ? ['Citron vert', 'Vanille', 'Fraise']
                          : ['Plus de fraîcheur', 'Je ne sais pas encore']
                      ).map((answer) => (
                        <button
                          key={answer}
                          onClick={() => void sendText(answer)}
                        >
                          {answer}
                          <ArrowRight size={12} aria-hidden="true" />
                        </button>
                      ))}
                      <button onClick={expert}>
                        En parler avec un expert{' '}
                        <ArrowRight size={12} aria-hidden="true" />
                      </button>
                    </div>
                  ) : null}
                </div>
                {view === 'refine' ? (
                  <ProjectSummary snapshot={snapshot} onEdit={edit} />
                ) : null}
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
          Ce prototype utilise des réponses et références fictives. Aucun débit
          réel, commercial contacté ou échantillon envoyé.
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
          Votre description et vos coordonnées restent dans la mémoire de cette
          page. Elles ne sont envoyées ni à une IA, ni à un commercial, et ne
          sont pas enregistrées en base.
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
