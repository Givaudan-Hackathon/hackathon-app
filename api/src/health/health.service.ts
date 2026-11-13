import { Inject, Injectable } from '@nestjs/common';
import pg from 'pg';
import { PG_POOL } from '../database/database.module.js';

@Injectable()
export class HealthService {
  constructor(@Inject(PG_POOL) private readonly pool: pg.Pool) {}

  async check() {
    const { rows } = await this.pool.query('SELECT version()');
    return {
      status: 'ok' as const,
      timestamp: new Date().toISOString(),
      db: rows[0].version as string,
    };
  }
}
