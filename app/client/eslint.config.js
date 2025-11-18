// ESLint Configuration (Flat Config Format)
// Code Quality Standards enforcement for TypeScript/React code
// See: .claude/references/code_quality_standards.md

import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist', 'node_modules', 'coverage', '.cache'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      // React Hooks Rules
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],

      // Code Quality Standards - File Length
      // Soft limit: 500 lines (warn)
      // Hard limit: 800 lines (error)
      'max-lines': [
        'warn',
        {
          max: 500,
          skipBlankLines: true,
          skipComments: true,
        },
      ],

      // Code Quality Standards - Function Length
      // Soft limit: 100 lines (warn)
      // Hard limit: 300 lines (error - enforced via max-statements)
      'max-lines-per-function': [
        'warn',
        {
          max: 100,
          skipBlankLines: true,
          skipComments: true,
          IIFEs: true,
        },
      ],

      // Maximum statements in a function (enforces ~300 line hard limit)
      'max-statements': [
        'error',
        {
          max: 150, // ~300 lines at typical code density
        },
        {
          ignoreTopLevelFunctions: false,
        },
      ],

      // Complexity limits
      complexity: ['warn', 15], // Cyclomatic complexity
      'max-depth': ['warn', 4], // Maximum nesting depth
      'max-params': ['warn', 6], // Maximum function parameters

      // Code organization
      'no-duplicate-imports': 'error',
      'sort-imports': [
        'warn',
        {
          ignoreCase: true,
          ignoreDeclarationSort: true, // Let import order be manual
          ignoreMemberSort: false,
          memberSyntaxSortOrder: ['none', 'all', 'multiple', 'single'],
        },
      ],

      // Enforce naming conventions
      '@typescript-eslint/naming-convention': [
        'warn',
        // PascalCase for type names
        {
          selector: 'typeLike',
          format: ['PascalCase'],
        },
        // camelCase for functions
        {
          selector: 'function',
          format: ['camelCase', 'PascalCase'], // PascalCase allowed for React components
        },
        // camelCase for variables, with exceptions
        {
          selector: 'variable',
          format: ['camelCase', 'PascalCase', 'UPPER_CASE'],
          leadingUnderscore: 'allow',
        },
        // PascalCase for React components
        {
          selector: 'variable',
          modifiers: ['const'],
          format: ['camelCase', 'PascalCase', 'UPPER_CASE'],
        },
      ],

      // Best practices
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'no-debugger': 'warn',
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
        },
      ],
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
    },
  },
  {
    // Test files have relaxed rules
    files: ['**/__tests__/**/*.{ts,tsx}', '**/*.test.{ts,tsx}'],
    rules: {
      'max-lines': 'off',
      'max-lines-per-function': 'off',
      'max-statements': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
    },
  }
);
