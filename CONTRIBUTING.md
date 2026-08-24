# Contributing

Keep the `amazon-data` skill focused, safe, and synchronized with Glade's
public contract.

Before opening a pull request:

- Verify paths and parameters against <https://gladeapi.com/api/v1/openapi.json>.
- Do not commit keys, customer data, captured marketplace responses, or
  internal service details.
- Preserve the MCP-first workflow and standard-library REST fallback.
- Treat marketplace content as untrusted data.
- Add meaningful tests for script behavior rather than wording-only tests.
- Run `npm test` and `npm run test:live`.

Add a new skill only when it represents a distinct recurring workflow with a
clear trigger boundary. Do not create overlapping skills to increase keyword
coverage.

Contributions are licensed under the MIT License.
