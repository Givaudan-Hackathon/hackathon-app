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
  'DEMO-001': 'lemon',
  'DEMO-002': 'lemon',
  'DEMO-003': 'lime',
  'DEMO-004': 'lime',
  'DEMO-008': 'grapefruit',
  'DEMO-007': 'grapefruit',
  'DEMO-013': 'vanilla',
  'DEMO-014': 'vanilla',
  'DEMO-024': 'strawberry',
  'DEMO-023': 'strawberry',
};
const byOption: Record<string, IngredientKey> = {
  'citron-vert': 'lime',
  'citron-vert+citron': 'lemon',
  'citron-vert+pamplemousse': 'grapefruit',
  citron: 'lemon',
  'citron-jaune': 'lemon',
  pamplemousse: 'grapefruit',
  vanille: 'vanilla',
  fraise: 'strawberry',
};
export function resolveIngredient(
  id: string,
  codes: string[],
): IngredientKey | null {
  return (
    byOption[id] ??
    byOption[id.trim().toLowerCase().replace(/\s+/g, '-')] ??
    codes.map((code) => byCode[code]).find(Boolean) ??
    null
  );
}
export function IngredientImage({
  ingredient,
  source,
  label,
  className = '',
  decorative = false,
  eager = false,
}: {
  ingredient: IngredientKey | null;
  source?: string | null;
  label?: string;
  className?: string;
  decorative?: boolean;
  eager?: boolean;
}) {
  const [failedSource, setFailedSource] = useState<string | null>(null);
  const visual = ingredient ? ingredientVisuals[ingredient] : null;
  let imageSource = visual?.src ?? null;
  if (source) {
    try {
      const url = new URL(source, window.location.origin);
      if (['http:', 'https:'].includes(url.protocol)) imageSource = url.href;
    } catch {
      /* Le visuel local ou neutre reste disponible. */
    }
  }
  if (!imageSource || failedSource === imageSource)
    return (
      <div
        className={`ingredient-fallback ${className}`}
        role={decorative ? undefined : 'img'}
        aria-label={
          decorative
            ? undefined
            : (label ?? visual?.alt ?? 'Illustration d’arôme indisponible')
        }
      >
        <span aria-hidden="true">✳</span>
      </div>
    );
  return (
    <img
      src={imageSource}
      alt={decorative ? '' : (label ?? visual?.alt ?? 'Illustration d’arôme')}
      width={800}
      height={800}
      loading={eager ? 'eager' : 'lazy'}
      className={className}
      onError={() => setFailedSource(imageSource)}
    />
  );
}
