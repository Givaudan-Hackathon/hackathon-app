import { IsString, IsOptional, MaxLength } from 'class-validator';

export class ConversationRequestDto {
  @IsString()
  @IsOptional()
  @MaxLength(64)
  session_id?: string | null;

  // Le message peut être vide SI un piste_id est fourni (géré par le service)
  @IsString()
  @IsOptional()
  @MaxLength(500)
  message?: string;

  @IsString()
  @IsOptional()
  @MaxLength(200)
  piste_id?: string | null;
}
