import { ArrowRight, Check, FileText, MessageCircle } from 'lucide-react';
import type { RequestReceipt } from '../../services/request-service.ts';
import { Button } from '../../components/ui/Button.tsx';

export function Confirmation({
  receipt,
  onRestart,
}: {
  receipt: RequestReceipt;
  onRestart: () => void;
}) {
  return (
    <section className="confirmation" aria-labelledby="confirmation-title">
      <span className="confirmation-check">
        <Check size={35} strokeWidth={1.5} aria-hidden="true" />
      </span>
      <span className="eyebrow">Votre idée a fait du chemin</span>
      <h1 id="confirmation-title">
        Votre demande
        <br />a été simulée.
      </h1>
      <p>
        Vous venez de parcourir les étapes d’un projet avec Givaudan.
        <br />
        Dans le service final, un expert examinera votre demande et vous
        recontactera pour préciser la suite.
      </p>
      <div className="confirmation-receipt">
        <FileText size={20} aria-hidden="true" />
        <span>
          Référence de démonstration<strong>{receipt.id}</strong>
        </span>
        <span>
          {new Intl.DateTimeFormat('fr-FR', {
            dateStyle: 'long',
            timeZone: 'Europe/Paris',
          }).format(new Date(receipt.createdAt))}
        </span>
      </div>
      <div className="confirmation-note">
        <MessageCircle size={19} aria-hidden="true" />
        <p>
          Aucun e-mail ni échantillon n’a été envoyé.
          <br />
          Votre demande ne constitue pas une commande.
        </p>
      </div>
      <Button onClick={onRestart}>
        Explorer une autre idée <ArrowRight size={17} aria-hidden="true" />
      </Button>
    </section>
  );
}
