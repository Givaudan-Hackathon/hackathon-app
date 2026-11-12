import { Module } from '@nestjs/common';
import { AppController } from './app.controller.js';
import { AppService } from './app.service.js';
import { DatabaseModule } from './database/database.module.js';
import { HealthController } from './health/health.controller.js';
import { HealthService } from './health/health.service.js';

@Module({
  imports: [DatabaseModule],
  controllers: [AppController, HealthController],
  providers: [AppService, HealthService],
})
export class AppModule {}
