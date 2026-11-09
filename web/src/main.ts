type Question = { id: number; question: string; answer: string };

const health = document.querySelector<HTMLParagraphElement>('#health')!;
const list = document.querySelector<HTMLUListElement>('#questions')!;

async function readJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Erreur HTTP ${response.status}`);
  return response.json();
}

async function refresh() {
  try {
    const status = await readJson<{ status: string; db: string }>('/api/health');
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
    health.textContent = "Impossible de charger les questions. Vérifier que l'API et la base sont démarrées.";
    console.error(error);
  }
}

void refresh();
