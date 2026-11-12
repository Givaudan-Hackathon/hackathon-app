import { useState } from 'react';

export const ingredientVisuals = {
  lemon: {
    src: new URL('../../assets/lemon.webp', import.meta.url).href,
    alt: 'Citron jaune et son zeste',
  },
  lime: {
    src: new URL('../../assets/lime.webp', import.meta.url).href,
    alt: 'Citron vert fraîchement coupé',
  },
  grapefruit: {
    src: new URL('../../assets/grapefruit.webp', import.meta.url).href,
    alt: 'Pamplemousse rose coupé en deux',
  },
  vanilla: {
    src: new URL('../../assets/vanilla.webp', import.meta.url).href,
    alt: 'Gousses et fleur de vanille',
  },
  strawberry: {
    src: new URL('../../assets/strawberry.webp', import.meta.url).href,
    alt: 'Fraises mûres et leurs feuilles',
  },
};
export type IngredientKey = keyof typeof ingredientVisuals;
const byCode: Record<string, IngredientKey> = {
  'DEMO-002': 'lemon',
  'DEMO-004': 'lime',
  'DEMO-008': 'grapefruit',
  'DEMO-014': 'vanilla',
  'DEMO-024': 'strawberry',
};
const byOption: Record<string, IngredientKey> = {
  'citron-vert': 'lime',
  'citron-vert+citron': 'lemon',
  'citron-vert+pamplemousse': 'grapefruit',
  citron: 'lemon',
  pamplemousse: 'grapefruit',
  vanille: 'vanilla',
  fraise: 'strawberry',
};
export function resolveIngredient(
  id: string,
  codes: string[],
): IngredientKey | null {
  return (
    byOption[id] ?? codes.map((code) => byCode[code]).find(Boolean) ?? null
  );
}
export function IngredientImage({
  ingredient,
  className = '',
  decorative = false,
  eager = false,
}: {
  ingredient: IngredientKey | null;
  className?: string;
  decorative?: boolean;
  eager?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  const visual = ingredient ? ingredientVisuals[ingredient] : null;
  if (failed || !visual)
    return (
      <div
        className={`ingredient-fallback ${className}`}
        role={decorative ? undefined : 'img'}
        aria-label={
          decorative
            ? undefined
            : (visual?.alt ?? 'Illustration d’arôme indisponible')
        }
      >
        <span aria-hidden="true">✳</span>
      </div>
    );
  return (
    <img
      src={visual.src}
      alt={decorative ? '' : visual.alt}
      width={800}
      height={800}
      loading={eager ? 'eager' : 'lazy'}
      className={className}
      onError={() => setFailed(true)}
    />
  );
}
