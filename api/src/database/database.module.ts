import { Module, Global } from '@nestjs/common';
import pg from 'pg';

export const PG_POOL = 'PG_POOL';

@Global()
@Module({
  providers: [
    {
      provide: PG_POOL,
      useFactory: (): pg.Pool => {
        const { DATABASE_URL } = process.env;
        if (!DATABASE_URL) {
          throw new Error(
            'DATABASE_URL manquante : copier api/.env.example dans api/.env.',
          );
        }
        const pool = new pg.Pool({ connectionString: DATABASE_URL });
        pool.on('error', (error) =>
          console.error('Connexion PostgreSQL :', error),
        );
        return pool;
      },
    },
  ],
  exports: [PG_POOL],
})
export class DatabaseModule {}
