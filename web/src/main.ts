type Question = { id: number; question: string; answer: string };

const health = document.querySelector<HTMLParagraphElement>('#health')!;
const list = document.querySelector<HTMLUListElement>('#questions')!;
const form = document.querySelector<HTMLFormElement>('form')!;
const button = form.querySelector<HTMLButtonElement>('button')!;
const submitStatus =
  document.querySelector<HTMLParagraphElement>('#submit-status')!;

async function readJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(
      typeof data?.error === 'string'
        ? data.error
        : `Erreur HTTP ${response.status}`,
    );
  }
  return data;
}
//Hell E
async function refresh() {
  try {
    const status = await readJson<{ status: string; db: string }>(
      '/api/health',
    );
    const questions = await readJson<Question[]>('/api/questions');
    health.textContent = `API OK · ${status.db}`;
    list.replaceChildren(
      ...questions.map((question) => {
        const item = document.createElement('li');
        item.textContent = `${question.question} → ${question.answer}`;
        return item;
      }),
    );
  } catch (error) {
    health.textContent =
      "Impossible de charger les questions. Vérifier que l'API et la base sont démarrées.";
    console.error(error);
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (button.disabled) return;
  const question = String(new FormData(form).get('question') ?? '').trim();
  if (!question) {
    submitStatus.textContent = 'Saisir une question.';
    return;
  }

  button.disabled = true;
  form.setAttribute('aria-busy', 'true');
  submitStatus.textContent =
    'Réponse en cours… Le premier appel peut prendre plus de temps.';
  try {
    await readJson<Question>('/api/questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    form.reset();
    submitStatus.textContent = 'Question et réponse enregistrées.';
    await refresh();
  } catch (error) {
    submitStatus.textContent =
      error instanceof Error
        ? error.message
        : "Impossible d'obtenir une réponse.";
    console.error(error);
  } finally {
    button.disabled = false;
    form.setAttribute('aria-busy', 'false');
  }
});

void refresh();
