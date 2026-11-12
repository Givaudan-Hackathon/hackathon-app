import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module.js';

// Charge api/.env avant toute lecture de process.env.
// npm -w api place le cwd à /workspace/api, donc loadEnvFile() trouve bien api/.env.
try {
  process.loadEnvFile();
} catch (error) {
  if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
}

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.setGlobalPrefix('api');
  await app.listen(process.env.PORT ?? 3000);
}
await bootstrap();
