import express, { type ErrorRequestHandler } from 'express';
import pg from 'pg';

// En production, la configuration peut venir directement de l'environnement.
try {
  process.loadEnvFile();
} catch (error) {
  if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
}

const { DATABASE_URL, AI_BASE_URL, AI_MODEL, AI_API_KEY = '' } = process.env;
if (!DATABASE_URL) {
  throw new Error(
    'DATABASE_URL manquante : copier api/.env.example dans api/.env.',
  );
}

const PORT = Number(process.env.PORT ?? 3000);
const db = new pg.Pool({ connectionString: DATABASE_URL });
db.on('error', (error) => console.error('Connexion PostgreSQL :', error));

const app = express();
app.use(express.json());

app.get('/api/health', async (_req, res) => {
  const { rows } = await db.query('SELECT version()');
  res.json({ status: 'ok', db: rows[0].version });
});

app.get('/api/questions', async (_req, res) => {
  const { rows } = await db.query(
    'SELECT id, question, answer, created_at FROM questions ORDER BY id DESC LIMIT 10',
  );
  res.json(rows);
});

app.post('/api/questions', async (req, res) => {
  const question =
    typeof req.body?.question === 'string' ? req.body.question.trim() : '';
  if (!question) {
    res
      .status(400)
      .json({ error: 'Question manquante : saisir une question.' });
    return;
  }

  const answer = await ask(question);
  const { rows } = await db.query(
    'INSERT INTO questions (question, answer) VALUES ($1, $2) RETURNING id, question, answer, created_at',
    [question, answer],
  );
  res.status(201).json(rows[0]);
});

class AIError extends Error {
  constructor(
    message: string,
    public status = 502,
  ) {
    super(message);
  }
}

// Appel compatible OpenAI de l'exemple du cours : l'URL et le modèle viennent du .env.
async function ask(question: string): Promise<string> {
  if (!AI_BASE_URL || !AI_MODEL) {
    throw new AIError(
      'IA non configurée : renseigner AI_BASE_URL et AI_MODEL dans api/.env.',
      503,
    );
  }

  try {
    const response = await fetch(
      `${AI_BASE_URL.replace(/\/+$/, '')}/chat/completions`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(AI_API_KEY ? { Authorization: `Bearer ${AI_API_KEY}` } : {}),
        },
        body: JSON.stringify({
          model: AI_MODEL,
          messages: [{ role: 'user', content: question }],
          stream: false,
        }),
        // Un serveur arrêté ou une génération bloquée ne doit pas attendre indéfiniment.
        signal: AbortSignal.timeout(60_000),
      },
    );
    if (!response.ok) {
      console.error(`IA : HTTP ${response.status}`);
      throw new AIError(
        "L'IA a refusé la demande. Vérifier le serveur et le modèle Ollama.",
      );
    }

    let data;
    try {
      data = await response.json();
    } catch (error) {
      if (error instanceof Error && error.name === 'TimeoutError') throw error;
      throw new AIError("L'IA a renvoyé une réponse JSON invalide.");
    }
    const answer = data?.choices?.[0]?.message?.content;
    if (typeof answer !== 'string' || !answer.trim()) {
      throw new AIError("L'IA n'a pas renvoyé de réponse textuelle.");
    }
    return answer.trim();
  } catch (error) {
    if (error instanceof AIError) throw error;
    if (error instanceof Error && error.name === 'TimeoutError') {
      throw new AIError(
        "L'IA n'a pas répondu dans les 60 secondes. Réessayer.",
        504,
      );
    }
    console.error('Connexion IA :', error);
    throw new AIError(
      'Ollama est injoignable. Vérifier son démarrage et AI_BASE_URL.',
      503,
    );
  }
}

const handleError: ErrorRequestHandler = (error, _req, res, _next) => {
  if (error instanceof AIError) {
    res.status(error.status).json({ error: error.message });
    return;
  }
  if (
    error instanceof SyntaxError &&
    'status' in error &&
    error.status === 400
  ) {
    res.status(400).json({ error: 'Corps JSON invalide.' });
    return;
  }
  console.error(error);
  res.status(500).json({ error: 'Impossible de traiter la demande.' });
};
app.use(handleError);

// Sans adresse explicite, Node écoute aussi hors du localhost du conteneur.
app.listen(PORT, () => console.log(`API sur http://localhost:${PORT}`));
