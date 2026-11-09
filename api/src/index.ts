import express, { type ErrorRequestHandler } from 'express';
import pg from 'pg';

// En production, la configuration peut venir directement de l'environnement.
try {
  process.loadEnvFile();
} catch (error) {
  if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
}

const { DATABASE_URL } = process.env;
if (!DATABASE_URL) {
  throw new Error('DATABASE_URL manquante : copier api/.env.example dans api/.env.');
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

const handleError: ErrorRequestHandler = (error, _req, res, _next) => {
  console.error(error);
  res.status(500).json({ error: 'Impossible de traiter la demande.' });
};
app.use(handleError);

// Sans adresse explicite, Node écoute aussi hors du localhost du conteneur.
app.listen(PORT, () => console.log(`API sur http://localhost:${PORT}`));
