module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:@typescript-eslint/recommended',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: ['react', 'react-hooks', '@typescript-eslint'],
  settings: {
    react: {
      version: 'detect',
    },
  },
  rules: {
    // Désactiver les règles trop strictes pour le développement
    'react/react-in-jsx-scope': 'off', // React 18 n'a pas besoin d'import React
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/no-explicit-any': 'warn',
    'react/prop-types': 'off', // On utilise TypeScript
    '@typescript-eslint/ban-ts-comment': 'warn',
    'no-console': 'off', // Autorisé pour le développement
  },
  ignorePatterns: ['node_modules/', 'dist/', 'build/', '*.config.js', '*.config.ts'],
};
