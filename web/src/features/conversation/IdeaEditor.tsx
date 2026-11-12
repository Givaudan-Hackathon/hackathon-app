import { ArrowRight } from 'lucide-react';
import { Button } from '../../components/ui/Button.tsx';
import hero from '../../assets/hero-citrus.webp';

export function IdeaEditor({
  value,
  pending,
  onChange,
  onContinue,
}: {
  value: string;
  pending: boolean;
  onChange: (value: string) => void;
  onContinue: () => void;
}) {
  return (
    <section className="idea-editor">
      <div>
        <h2>Votre idée est le point de départ.</h2>
        <p>
          Retrouvez votre description, ajustez-la et poursuivez votre projet. Un
          changement actualisera les propositions et vous invitera à confirmer
          votre nouveau choix.
        </p>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            onContinue();
          }}
        >
          <label htmlFor="project-idea">Décrivez votre projet</label>
          <textarea
            id="project-idea"
            name="projectIdea"
            value={value}
            onChange={(event) => onChange(event.target.value)}
            required
            minLength={1}
            maxLength={500}
            rows={5}
            disabled={pending}
          />
          <span className="idea-editor-count">{value.length}/500</span>
          <Button type="submit" loading={pending}>
            Poursuivre avec cette idée{' '}
            <ArrowRight size={16} aria-hidden="true" />
          </Button>
        </form>
      </div>
      <img src={hero} width={1024} height={1280} alt="" />
    </section>
  );
}
