import { Body, Controller, Post, ValidationPipe } from '@nestjs/common';
import { ConversationService } from './conversation.service.js';
import { ConversationRequestDto } from './dto/conversation-request.dto.js';

@Controller('conversation')
export class ConversationController {
  constructor(private readonly conversationService: ConversationService) {}

  @Post()
  async conversation(@Body(ValidationPipe) dto: ConversationRequestDto) {
    return this.conversationService.relayToPython(dto);
  }
}