module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat', 'fix', 'docs', 'style', 'refactor', 'perf',
        'test', 'build', 'ci', 'chore', 'revert', 'quantum',
        'security', 'zkp', 'pqc', 'face-ml', 'infra',
      ],
    ],
    'scope-enum': [
      2,
      'always',
      [
        'auth-api', 'face-ml', 'zk-proofs', 'quantum-rng',
        'quantum-qkd', 'quantum-ml', 'quantum-cudaq', 'pqc-crypto',
        'cache-store', 'vector-db', 'analytics', 'edge-gateway',
        'proto', 'pkg', 'deploy', 'ci', 'docs', 'tests',
        'terraform', 'pulumi', 'helm', 'istio', 'observability',
      ],
    ],
    'subject-case': [2, 'never', ['start-case', 'pascal-case', 'upper-case']],
  },
};
