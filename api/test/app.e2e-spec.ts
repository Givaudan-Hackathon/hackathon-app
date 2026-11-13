import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { App } from 'supertest/types.js';
import { AppModule } from './../src/app.module.js';
import { PG_POOL } from './../src/database/database.module.js';

describe('AppController (e2e)', () => {
  let app: INestApplication<App>;

  const fakePool = {
    query: async () => ({ rows: [{ version: 'PostgreSQL test' }] }),
  };

  beforeEach(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(PG_POOL)
      .useValue(fakePool)
      .compile();

    app = moduleFixture.createNestApplication();
    app.setGlobalPrefix('api');
    await app.init();
  });

  it('/api (GET) → Hello World!', () => {
    return request(app.getHttpServer())
      .get('/api')
      .expect(200)
      .expect('Hello World!');
  });

  it('/api/health (GET) → contrat Sante', async () => {
    const res = await request(app.getHttpServer())
      .get('/api/health')
      .expect(200);

    expect(res.body).toMatchObject({ status: 'ok' });
    expect(typeof res.body.db).toBe('string');
    expect(typeof res.body.timestamp).toBe('string');
  });

  afterEach(async () => {
    if (app) await app.close();
  });
});
