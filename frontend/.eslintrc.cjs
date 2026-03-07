/* eslint-env node */
/**
 * ESLint 配置 — Vue 3 + JavaScript (渐进式引入 TypeScript)
 * 运行: npx eslint src/ --ext .vue,.js,.ts
 */
module.exports = {
    root: true,
    env: {
        browser: true,
        es2022: true,
        node: true,
    },
    extends: [
        'eslint:recommended',
        'plugin:vue/vue3-recommended',
        'prettier', // 必须放最后，关闭与 Prettier 冲突的规则
    ],
    parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
    },
    rules: {
        // ── 渐进式宽松规则（避免初期太多报错）──────────────
        'vue/multi-word-component-names': 'off',       // 允许单词组件名 (Header, Sidebar)
        'vue/no-unused-vars': 'warn',                  // 未使用变量降为警告
        'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
        'no-console': ['warn', { allow: ['warn', 'error'] }],
        'vue/require-default-prop': 'off',             // 不强制 prop 默认值
        'vue/max-attributes-per-line': 'off',          // 不强制属性换行
        'vue/singleline-html-element-content-newline': 'off',
    },
};
