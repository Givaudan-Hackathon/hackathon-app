import { HttpException, Inject, Injectable } from '@nestjs/common';
import pg from 'pg';
import { PG_POOL } from '../database/database.module.js';

export interface Exchange {
  id: number;
  question: string;
  answer: string;
  created_at: string;
}

@Injectable()
export class QuestionsService {
  constructor(@Inject(PG_POOL) private readonly pool: pg.Pool) {}

  async findLatest(): Promise<Exchange[]> {
    const { rows } = await this.pool.query(
      'SELECT id, question, answer, created_at FROM questions ORDER BY id DESC LIMIT 10',
    );
    return rows;
  }

  async create(rawQuestion: unknown): Promise<Exchange> {
    const question = typeof rawQuestion === 'string' ? rawQuestion.trim() : '';
    if (!question) {
      throw new HttpException('Question manquante : saisir une question.', 400);
    }

    const answer = await this.ask(question);
    const { rows } = await this.pool.query(
      'INSERT INTO questions (question, answer) VALUES ($1, $2) RETURNING id, question, answer, created_at',
      [question, answer],
    );
    return rows[0];
  }

  private async ask(question: string): Promise<string> {
    const { AI_BASE_URL, AI_MODEL, AI_API_KEY = '' } = process.env;

    if (!AI_BASE_URL || !AI_MODEL) {
      throw new HttpException(
        'IA non configurée : renseigner AI_BASE_URL et AI_MODEL dans api/.env.',
        503,
      );
    }

    let response: Response;
    try {
      response = await fetch(
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
          signal: AbortSignal.timeout(60_000),
        },
      );
    } catch (error) {
      if (error instanceof Error && error.name === 'TimeoutError') {
        throw new HttpException(
          "L'IA n'a pas répondu dans les 60 secondes. Réessayer.",
          504,
        );
      }
      console.error('Connexion IA :', error);
      throw new HttpException(
        'Ollama est injoignable. Vérifier son démarrage et AI_BASE_URL.',
        503,
      );
    }

    if (!response.ok) {
      console.error(`IA : HTTP ${response.status}`);
      throw new HttpException(
        "L'IA a refusé la demande. Vérifier le serveur et le modèle Ollama.",
        502,
      );
    }

    let data: { choices?: { message?: { content?: unknown } }[] };
    try {
      data = await response.json();
    } catch {
      throw new HttpException("L'IA a renvoyé une réponse JSON invalide.", 502);
    }

    const answer = data?.choices?.[0]?.message?.content;
    if (typeof answer !== 'string' || !answer.trim()) {
      throw new HttpException(
        "L'IA n'a pas renvoyé de réponse textuelle.",
        502,
      );
    }
    return answer.trim();
  }
}
