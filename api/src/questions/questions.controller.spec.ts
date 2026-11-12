import { Test } from '@nestjs/testing';
import { PG_POOL } from '../database/database.module.js';
import { QuestionsController } from './questions.controller.js';
import { QuestionsService } from './questions.service.js';

describe('QuestionsController', () => {
  let controller: QuestionsController;

  const fakePool = {
    query: async (sql: string) => {
      if (sql.startsWith('SELECT')) {
        return {
          rows: [
            {
              id: 1,
              question: 'q',
              answer: 'a',
              created_at: '2026-11-12T00:00:00Z',
            },
          ],
        };
      }
      return {
        rows: [
          {
            id: 2,
            question: 'q',
            answer: 'a',
            created_at: '2026-11-12T00:00:00Z',
          },
        ],
      };
    },
  };

  beforeEach(async () => {
    const moduleRef = await Test.createTestingModule({
      controllers: [QuestionsController],
      providers: [QuestionsService, { provide: PG_POOL, useValue: fakePool }],
    }).compile();

    controller = moduleRef.get(QuestionsController);
  });

  it('GET returns an array', async () => {
    const res = await controller.list();
    expect(Array.isArray(res)).toBe(true);
  });

  it('POST rejects empty question with 400', async () => {
    await expect(controller.create({ question: '   ' })).rejects.toMatchObject({
      status: 400,
      message: 'Question manquante : saisir une question.',
    });
  });
});
