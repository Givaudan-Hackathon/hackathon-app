import { Body, Controller, Get, Post } from '@nestjs/common';
import { QuestionsService } from './questions.service.js';

@Controller('questions')
export class QuestionsController {
  constructor(private readonly questions: QuestionsService) {}

  @Get()
  list() {
    return this.questions.findLatest();
  }

  @Post()
  create(@Body() body: { question?: unknown }) {
    return this.questions.create(body?.question);
  }
}
