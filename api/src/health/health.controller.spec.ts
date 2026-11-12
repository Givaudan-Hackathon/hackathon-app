import { Test } from '@nestjs/testing';
import { PG_POOL } from '../database/database.module.js';
import { HealthController } from './health.controller.js';
import { HealthService } from './health.service.js';

describe('HealthController', () => {
  let controller: HealthController;

  const fakePool = {
    query: async () => ({ rows: [{ version: 'PostgreSQL 17.11' }] }),
  };

  beforeEach(async () => {
    const moduleRef = await Test.createTestingModule({
      controllers: [HealthController],
      providers: [HealthService, { provide: PG_POOL, useValue: fakePool }],
    }).compile();

    controller = moduleRef.get(HealthController);
  });

  it('returns status, timestamp and db', async () => {
    const res = await controller.check();
    expect(res.status).toBe('ok');
    expect(typeof res.timestamp).toBe('string');
    expect(res.db).toBe('PostgreSQL 17.11');
  });
});
