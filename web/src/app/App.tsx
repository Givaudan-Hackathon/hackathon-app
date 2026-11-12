import { useEffect, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CircleHelp,
  Leaf,
  RotateCcw,
} from 'lucide-react';
import { Brand } from '../components/ui/Brand.tsx';
import { Button } from '../components/ui/Button.tsx';
import { Dialog } from '../components/ui/Dialog.tsx';
import { useConversation } from '../features/conversation/useConversation.ts';
import { ConversationPanel } from '../features/conversation/ConversationPanel.tsx';
import { ProjectSummary } from '../features/conversation/ProjectSummary.tsx';
import { OptionCards } from '../features/recommendations/OptionCards.tsx';
import { BriefReview } from '../features/request/BriefReview.tsx';
import { RequestForm } from '../features/request/RequestForm.tsx';
import { Confirmation } from '../features/request/Confirmation.tsx';
import { createMockConversationService } from '../services/adapters/mock-conversation.ts';
import { createMockRequestService } from '../services/adapters/mock-request.ts';
import type { RequestReceipt } from '../services/request-service.ts';
import type { FlavorOption } from '../services/conversation-service.ts';
import { Home } from './Home.tsx';

type View = 'home' | 'project' | 'request' | 'done';
export function App() {
  const [services] = useState(() => ({
    conversation: createMockConversationService(),
    request: createMockRequestService(),
  }));
  const { state, send, reset } = useConversation(services.conversation);
  const [view, setView] = useState<View>('home');
  const [dialog, setDialog] = useState<'help' | 'reset' | 'privacy' | null>(
    null,
  );
  const [kind, setKind] = useState<'sample' | 'expert'>('sample');
  const [receipt, setReceipt] = useState<RequestReceipt | null>(null);
  const step =
    view === 'done' || view === 'request'
      ? 3
      : state.snapshot?.etape === 'pistes'
        ? 2
        : state.snapshot?.brief
          ? 3
          : 1;
  const snapshot = state.snapshot;
  const hasProject = state.messages.length > 0 && view !== 'done';
  useEffect(() => {
    document.title =
      view === 'home'
        ? 'Givaudan — Le goût de vos idées'
        : view === 'done'
          ? 'Demande simulée — Givaudan'
          : 'Votre projet — Givaudan';
    if (view !== 'home')
      document
        .querySelector<HTMLElement>('main h1')
        ?.focus({ preventScroll: true });
  }, [view]);
  useEffect(() => {
    if (!hasProject) return;
    const guard = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    window.addEventListener('beforeunload', guard);
    return () => window.removeEventListener('beforeunload', guard);
  }, [hasProject]);
  function changeView(next: View) {
    setView(next);
    window.scrollTo({ top: 0, behavior: 'instant' });
  }
  function startFresh() {
    reset();
    setReceipt(null);
    setKind('sample');
    setDialog(null);
    changeView('home');
  }
  function home() {
    if (hasProject) setDialog('reset');
    else startFresh();
  }
  function edit() {
    changeView('project');
    requestAnimationFrame(() => {
      const disclosure = document.querySelector<HTMLDetailsElement>(
        '.chat-composer-disclosure',
      );
      if (disclosure) disclosure.open = true;
      document
        .querySelector<HTMLTextAreaElement>('.chat-composer textarea')
        ?.focus({ preventScroll: false });
    });
  }
  async function sendText(message: string) {
    const result = await send(message);
    if (result?.etape === 'echantillons') {
      setKind('sample');
      changeView('request');
    }
    return Boolean(result);
  }
  function start(message: string) {
    changeView('project');
    void sendText(message);
  }
  function choose(piste: FlavorOption) {
    void send('', piste.id, `Je choisis ${piste.nom}.`);
  }
  function expert() {
    setKind('expert');
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
            <nav className="stepper" aria-label="Progression du projet">
              <ol>
                {['Votre idée', 'Affiner', 'Choisir', 'Votre demande'].map(
                  (label, index) => (
                    <li
                      key={label}
                      className={
                        index === step
                          ? 'is-current'
                          : index < step
                            ? 'is-complete'
                            : ''
                      }
                      aria-current={index === step ? 'step' : undefined}
                      aria-label={`${index + 1}. ${label}`}
                    >
                      <span className="step-number">
                        {index < step ? (
                          <Check size={12} aria-hidden="true" />
                        ) : (
                          index + 1
                        )}
                      </span>
                      <span className="step-label">{label}</span>
                    </li>
                  ),
                )}
              </ol>
            </nav>
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
          — échanges et demandes simulés
        </span>
      </div>
      <main id="main">
        {view === 'home' ? <Home onStart={start} /> : null}
        {view === 'project' ? (
          <div className="workspace page-shell">
            <div className="workspace-top">
              <button className="text-button" onClick={home}>
                <ArrowLeft size={15} aria-hidden="true" /> Nouvelle idée
              </button>
              <span>Votre projet, à votre rythme</span>
            </div>
            <div className="workspace-title">
              <div>
                <span className="eyebrow">Créons les bonnes connexions</span>
                <h1 tabIndex={-1}>
                  {snapshot?.brief
                    ? 'Votre projet se précise.'
                    : snapshot?.etape === 'pistes'
                      ? 'Les possibilités prennent goût.'
                      : 'Faisons grandir votre idée.'}
                </h1>
              </div>
              <span className="workspace-step">Étape {step + 1} sur 4</span>
            </div>
            <div className="workspace-grid">
              <div className="workspace-content">
                <ConversationPanel state={state} onSend={sendText} />
                {snapshot?.etape === 'pistes' ? (
                  <OptionCards
                    snapshot={snapshot}
                    pending={state.pending}
                    onSelect={choose}
                    onReject={() =>
                      void sendText('Aucun de ces arômes ne me convient.')
                    }
                    onExpert={expert}
                  />
                ) : null}
                {snapshot?.brief ? (
                  <BriefReview
                    snapshot={snapshot}
                    pending={state.pending}
                    onContinue={() =>
                      void sendText(
                        'Je souhaite préparer ma demande d’échantillon.',
                      )
                    }
                    onEdit={edit}
                  />
                ) : null}
                {snapshot?.etape === 'relance' && !state.pending ? (
                  <div className="quick-answers">
                    <span>Pour vous aider :</span>
                    {(!snapshot.compris.type_produit
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
              <ProjectSummary snapshot={snapshot} onEdit={edit} />
            </div>
          </div>
        ) : null}
        {(snapshot?.echantillons || kind === 'expert') && view !== 'done' ? (
          <div hidden={view !== 'request'} className="page-shell request-page">
            <div className="workspace-top">
              <button
                className="text-button"
                onClick={() => changeView('project')}
              >
                <ArrowLeft size={15} aria-hidden="true" /> Mon projet
              </button>
              <span>Étape 4 sur 4</span>
            </div>
            <h1 className="sr-only" tabIndex={-1}>
              Préparer votre demande
            </h1>
            <RequestForm
              key={`${kind}-${JSON.stringify(snapshot?.brief ?? null)}`}
              service={services.request}
              brief={snapshot?.brief ?? null}
              projectDescription={projectDescription}
              kind={kind}
              onComplete={complete}
              onBack={() => changeView('project')}
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
          <li>Choisissez une proposition ou demandez l’avis d’un expert.</li>
          <li>Relisez votre projet et simulez une demande.</li>
        </ol>
        <div className="notice">
          Ce prototype utilise des réponses et références fictives. Aucun
          commercial n’est contacté et aucun échantillon n’est envoyé.
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
          Recharger ou quitter la page réinitialise la démonstration. Vous
          pouvez utiliser des coordonnées fictives pour tester le parcours.
        </p>
        <Button onClick={() => setDialog(null)}>Fermer</Button>
      </Dialog>
      <Dialog
        open={dialog === 'reset'}
        onClose={() => setDialog(null)}
        title="Explorer une nouvelle idée ?"
      >
        <p>
          Le projet en cours sera réinitialisé. Vous pourrez démarrer une
          nouvelle conversation à partir d’une autre envie.
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
