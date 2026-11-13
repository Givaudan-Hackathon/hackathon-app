import { useId, useState, type FormEvent } from 'react';
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  Check,
  MessageCircle,
  SlidersHorizontal,
  Sparkles,
} from 'lucide-react';
import { Button } from '../components/ui/Button.tsx';
import {
  IngredientImage,
  type IngredientKey,
} from '../features/recommendations/IngredientImage.tsx';

const ingredients: {
  key: IngredientKey;
  label: string;
  description: string;
  example: string;
}[] = [
  {
    key: 'lime',
    label: 'Citron vert',
    description: 'Vif & rafraîchissant',
    example:
      'Je crée une boisson pétillante au citron vert, fraîche et peu sucrée.',
  },
  {
    key: 'lemon',
    label: 'Citron jaune',
    description: 'Zesté & lumineux',
    example: 'Je prépare un biscuit au citron jaune, gourmand et peu sucré.',
  },
  {
    key: 'grapefruit',
    label: 'Pamplemousse',
    description: 'Fruité & singulier',
    example: 'Je crée une boisson au pamplemousse, avec une légère amertume.',
  },
  {
    key: 'vanilla',
    label: 'Vanille',
    description: 'Ronde & enveloppante',
    example: 'Je prépare un dessert végétal à la vanille, doux et gourmand.',
  },
  {
    key: 'strawberry',
    label: 'Fraise',
    description: 'Juteuse & généreuse',
    example: 'Je crée un yaourt à la fraise, fruité et peu sucré.',
  },
];

export function Home({ onStart }: { onStart: (description: string) => void }) {
  const [description, setDescription] = useState('');
  const id = useId();
  function start(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (description.trim()) onStart(description.trim());
  }
  return (
    <>
      <section className="hero page-shell" aria-labelledby="hero-title">
        <div className="hero-copy">
          <span className="eyebrow">
            <span className="small-spark">
              <Sparkles size={14} aria-hidden="true" />
            </span>{' '}
            Le goût de vos idées
          </span>
          <h1 id="hero-title">
            Vos idées ont
            <br />
            de la saveur.
            <br />
            Donnons-leur vie.
          </h1>
          <p className="hero-intro">
            Une boisson, un dessert, une envie nouvelle…
            <br className="desktop-break" /> Décrivez votre projet. Explorons
            les arômes qui lui ressemblent.
          </p>
          <form onSubmit={start} className="idea-form">
            <label htmlFor={id}>Qu’avez-vous envie de créer ?</label>
            <div className="idea-input-wrap">
              <textarea
                id={id}
                name="project"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                required
                maxLength={500}
                rows={3}
                placeholder="Une boisson pétillante au citron vert, fraîche et peu sucrée…"
              />
              <button
                className="send-button"
                type="submit"
                aria-label="Explorer les arômes de mon projet"
              >
                <ArrowUpRight size={25} strokeWidth={1.6} aria-hidden="true" />
              </button>
            </div>
            <div className="idea-form-bottom">
              <span>
                <Check size={13} aria-hidden="true" /> Pas besoin de fiche
                technique
              </span>
              <span>{description.length}/500</span>
            </div>
          </form>
          <div className="example-row">
            <span>Besoin d’inspiration ?</span>
            <button onClick={() => onStart(ingredients[0].example)}>
              Une boisson fraîche <ArrowUpRight size={13} aria-hidden="true" />
            </button>
            <button onClick={() => onStart(ingredients[3].example)}>
              Un dessert végétal <ArrowUpRight size={13} aria-hidden="true" />
            </button>
          </div>
        </div>
        <div className="hero-art">
          <div className="hero-photo-wrap">
            <img
              src={new URL('../assets/hero-citrus.webp', import.meta.url).href}
              width={1024}
              height={1280}
              alt="Citrons verts fraîchement coupés, citron jaune et feuilles d’agrumes"
              className="hero-photo"
              fetchPriority="high"
            />
          </div>
          <div className="hero-note">
            <span className="note-icon">
              <Sparkles size={21} strokeWidth={1.5} aria-hidden="true" />
            </span>
            <div>
              <strong>Tout commence par une envie.</strong>
              <span>La vôtre, on a hâte de la découvrir.</span>
            </div>
          </div>
          <button
            className="hero-flavor-tag"
            onClick={() => onStart(ingredients[0].example)}
          >
            <span className="tag-dot" /> Envie de fraîcheur ?{' '}
            <ArrowUpRight size={16} aria-hidden="true" />
          </button>
          <span className="hero-art-label">La nature comme inspiration.</span>
        </div>
      </section>
      <div className="hero-bottom page-shell">
        <span>
          <span className="online-dot" /> Un premier pas, sans engagement
        </span>
        <a href="#comment-ca-marche">
          Découvrez le parcours <ArrowDown size={15} aria-hidden="true" />
        </a>
        <span className="hero-bottom-right">
          L’inspiration vous appartient.
        </span>
      </div>
      <section
        id="comment-ca-marche"
        className="how-section"
        aria-labelledby="how-title"
      >
        <div className="page-shell">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Simplement, à votre rythme</span>
              <h2 id="how-title">D’une idée à votre prochain arôme.</h2>
            </div>
            <p>
              Quelques échanges pour préciser votre envie.
              <br />
              Un expert pour vous accompagner ensuite.
            </p>
          </div>
          <div className="how-grid">
            {[
              {
                icon: MessageCircle,
                title: 'Racontez votre idée',
                text: 'Votre produit, le goût recherché, ce qui compte pour vous. Avec vos mots.',
              },
              {
                icon: SlidersHorizontal,
                title: 'Explorons les possibilités',
                text: 'Affinez votre besoin et découvrez des pistes expliquées, faciles à comparer.',
              },
              {
                icon: Sparkles,
                title: 'Préparez la suite',
                text: 'Relisez votre projet et préparez une demande à examiner avec un expert.',
              },
            ].map(({ icon: Icon, title, text }, i) => (
              <div className="how-item" key={title}>
                <span className="how-number">0{i + 1}</span>
                <Icon size={25} strokeWidth={1.3} aria-hidden="true" />
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
      <section
        id="nos-aromes"
        className="ingredient-section page-shell"
        aria-labelledby="ingredients-title"
      >
        <div className="section-heading">
          <div>
            <span className="eyebrow">Une première palette à explorer</span>
            <h2 id="ingredients-title">Quelle sera votre inspiration ?</h2>
          </div>
          <p>
            Cinq ingrédients pour imaginer votre projet.
            <br />
            Des références fictives pour cette démonstration.
          </p>
        </div>
        <div className="ingredient-grid">
          {ingredients.map((ingredient) => (
            <button
              className="ingredient-tile"
              key={ingredient.key}
              onClick={() => onStart(ingredient.example)}
            >
              <div className="ingredient-photo">
                <IngredientImage ingredient={ingredient.key} decorative />
                <span className="ingredient-link">
                  <ArrowUpRight size={19} aria-hidden="true" />
                </span>
              </div>
              <strong>{ingredient.label}</strong>
              <span>{ingredient.description}</span>
            </button>
          ))}
        </div>
        <div className="ingredient-cta">
          <p>Vous avez déjà une idée en tête ?</p>
          <Button
            variant="secondary"
            onClick={() =>
              document
                .querySelector<HTMLTextAreaElement>('.idea-form textarea')
                ?.focus()
            }
          >
            Décrire mon projet <ArrowRight size={17} aria-hidden="true" />
          </Button>
        </div>
      </section>
    </>
  );
}
