// @ts-check
import eslint from '@eslint/js';
import { defineConfig, globalIgnores } from 'eslint/config';
import prettier from 'eslint-config-prettier/flat';
import tseslint from 'typescript-eslint';

export default defineConfig(
  // db/data : les fichiers de PostgreSQL, illisibles hors de son conteneur
  // .venv : les paquets Python de l'équipe Data/IA
  globalIgnores(['**/dist/', 'db/data/', '**/.venv/', '**/.scratch/**']),
  eslint.configs.recommended,
  tseslint.configs.recommended,
  // Désactive les règles de forme : c'est le travail de Prettier
  prettier,
  {
    // Express exige quatre paramètres pour reconnaître un middleware d'erreur.
    // Le préfixe _ signale les paramètres volontairement inutilisés.
    rules: {
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_' },
      ],
    },
  },
);
