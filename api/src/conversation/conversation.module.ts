import { Module } from '@nestjs/common';
import { ConversationController } from './conversation.controller.js';
import { ConversationService } from './conversation.service.js';

@Module({
  controllers: [ConversationController],
  providers: [ConversationService],
})
export class ConversationModule {}
