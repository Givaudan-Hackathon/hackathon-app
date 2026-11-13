import { Body, Controller, HttpCode, Inject, Post } from '@nestjs/common';
import { ConversationService } from './conversation.service.js';
import { ConversationRequestDto } from './dto/conversation-request.dto.js';

@Controller('conversation')
export class ConversationController {
  constructor(
    @Inject(ConversationService)
    private readonly conversationService: ConversationService,
  ) {}

  @Post()
  @HttpCode(200)
  async conversation(@Body() dto: ConversationRequestDto) {
    return this.conversationService.relayToPython(dto);
  }
}
