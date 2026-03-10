module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
    node: true,
    jest: true,
  },
  extends: [
    'react-app',
    'react-app/jest',
  ],
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  rules: {
    // 禁止使用 console
    'no-console': ['warn', { allow: ['warn', 'error'] }],

    // React 相关规则
    'react/react-in-jsx-scope': 'off',
    'react/prop-types': 'off',

    // 通用规则
    'no-param-reassign': ['warn', { props: false }],
    'prefer-destructuring': ['warn', { object: true, array: false }],
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
  overrides: [
    {
      // 测试文件中允许使用 console
      files: ['**/__tests__/**/*', '**/*.test.ts', '**/*.test.tsx', '**/*.spec.ts', '**/*.spec.tsx'],
      rules: {
        'no-console': 'off',
      },
    },
  ],
  ignorePatterns: ['build', 'dist', 'node_modules', 'coverage', '*.config.js'],
};
