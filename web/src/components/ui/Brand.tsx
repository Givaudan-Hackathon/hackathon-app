import { Sprout } from 'lucide-react';

export function Brand({ onClick }: { onClick: () => void }) {
  return (
    <button
      className="brand"
      onClick={onClick}
      aria-label="Givaudan — revenir à l’accueil"
    >
      <Sprout
        className="brand-symbol"
        size={32}
        strokeWidth={1.5}
        aria-hidden="true"
      />
      <span>
        <span className="brand-name" translate="no">
          givaudan
        </span>
        <span className="brand-tagline">Taste & Wellbeing</span>
      </span>
    </button>
  );
}
