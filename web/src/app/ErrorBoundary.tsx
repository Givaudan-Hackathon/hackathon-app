import { Component, type ReactNode } from 'react';
import { Button } from '../components/ui/Button.tsx';

export class ErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    if (this.state.failed)
      return (
        <main className="error-page">
          <h1>Reprenons votre projet.</h1>
          <p>
            L’interface n’a pas pu s’afficher. Rechargez cette page pour
            démarrer une nouvelle démonstration.
          </p>
          <Button onClick={() => window.location.reload()}>
            Recharger la page
          </Button>
        </main>
      );
    return this.props.children;
  }
}
