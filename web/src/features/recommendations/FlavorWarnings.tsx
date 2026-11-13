import { TriangleAlert } from 'lucide-react';
import type { FlavorOption } from '../../services/conversation-service.ts';

export function FlavorWarnings({
  missing = [],
  labels = [],
}: {
  missing?: string[];
  labels?: FlavorOption['references_sans_label'];
}) {
  return (
    <div className="flavor-warnings">
      {[...new Set(missing)].map((arome) => (
        <p key={arome}>
          <TriangleAlert size={16} aria-hidden="true" />
          <span>{arome} : référence à créer sur mesure avec un expert.</span>
        </p>
      ))}
      {labels.map((item) => (
        <p key={`${item.code}-${item.label_manquant}`}>
          <TriangleAlert size={16} aria-hidden="true" />
          <span>
            Label {item.label_manquant} non renseigné pour {item.arome} (
            {item.code}). À vérifier avec un expert.
          </span>
        </p>
      ))}
    </div>
  );
}
