import { Test } from '@nestjs/testing';
import type { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { ConversationController } from './conversation.controller.js';
import { ConversationService } from './conversation.service.js';

it('POST /api/conversation renvoie 200 et le snapshot', async () => {
  const data = { session_id: 'test', etape: 'relance', reponse: 'Quel goût ?' };
  const module = await Test.createTestingModule({
    controllers: [ConversationController],
    providers: [
      {
        provide: ConversationService,
        useValue: { relayToPython: async () => data },
      },
    ],
  }).compile();
  const app: INestApplication = module.createNestApplication();
  app.setGlobalPrefix('api');
  await app.init();
  try {
    await request(app.getHttpServer())
      .post('/api/conversation')
      .send({ message: 'Bonjour' })
      .expect(200)
      .expect(data);
  } finally {
    await app.close();
  }
});
