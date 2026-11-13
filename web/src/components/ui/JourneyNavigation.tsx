import { useEffect, useId, useRef } from 'react';
import { Check } from 'lucide-react';
import type { JourneyPage, JourneyStep } from '../../app/journey.ts';

export function JourneyNavigation({
  steps,
  current,
  pending,
  finished,
  onNavigate,
}: {
  steps: JourneyStep[];
  current: JourneyPage;
  pending: boolean;
  finished: boolean;
  onNavigate: (page: JourneyPage) => void;
}) {
  const id = useId();
  const navRef = useRef<HTMLElement>(null);
  const active = steps.findIndex((step) => step.id === current);
  useEffect(() => {
    const nav = navRef.current;
    const button = nav?.querySelector<HTMLElement>('[aria-current="step"]');
    // Ne fait défiler que la bande horizontale, sans déplacer le contenu.
    if (nav && button)
      nav.scrollLeft =
        button.offsetLeft - nav.clientWidth / 2 + button.clientWidth / 2;
  }, [current]);
  return (
    <div className="journey-bar">
      <div className="page-shell journey-status" role="status">
        <span>
          {finished
            ? 'Parcours terminé'
            : `Étape ${active + 1} sur ${steps.length}`}
        </span>
        <strong>
          {finished ? 'Votre demande a été simulée' : steps[active].label}
        </strong>
        <span className="journey-guidance">
          Vous pouvez revenir sur les étapes disponibles.
        </span>
      </div>
      <nav
        ref={navRef}
        className="journey-nav page-shell"
        aria-label="Étapes de votre projet"
      >
        <ol>
          {steps.map((step, index) => (
            <li
              key={step.id}
              className={`${step.id === current ? 'is-current' : ''} ${step.completed ? 'is-complete' : ''} ${step.skipped ? 'is-skipped' : ''}`}
            >
              <button
                type="button"
                onClick={() => onNavigate(step.id)}
                disabled={pending || finished || !step.available}
                aria-current={step.id === current ? 'step' : undefined}
                aria-label={`${index + 1}. ${step.label}`}
                aria-describedby={`${id}-${step.id}`}
                title={
                  step.available
                    ? `Revenir à ${step.label.toLowerCase()}`
                    : step.hint
                }
              >
                <span className="journey-number">
                  {step.completed ? (
                    <Check size={17} aria-hidden="true" />
                  ) : (
                    index + 1
                  )}
                </span>
                <span className="journey-label">
                  {step.label}
                  <small>
                    {step.skipped
                      ? 'Non requis'
                      : step.id === current && !finished
                        ? 'En cours'
                        : step.completed
                          ? 'Complétée'
                          : step.available
                            ? 'Accessible'
                            : 'À venir'}
                  </small>
                </span>
              </button>
              <span className="sr-only" id={`${id}-${step.id}`}>
                {step.skipped || !step.available
                  ? step.hint
                  : step.completed
                    ? 'Étape complétée.'
                    : 'Étape accessible.'}
              </span>
            </li>
          ))}
        </ol>
      </nav>
    </div>
  );
}
