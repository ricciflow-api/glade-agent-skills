# Glade agent skills

Installable agent skills for researching public Amazon marketplace data through
[Glade API](https://gladeapi.com). The repository currently provides one
focused skill, `amazon-data`, with an MCP-first workflow and a zero-dependency
Python REST fallback.

## Available skill

| Skill | Use it for |
|---|---|
| [`amazon-data`](skills/amazon-data) | Products, search, offers, reviews, sellers, categories, deals, best sellers, identifiers, stock, and sales estimates |

The skill intentionally does not cover private Amazon account, order,
advertising, or Seller Central data.

## Install in Codex

Ask Codex's built-in installer to install `amazon-data` from this repository:

```text
$skill-installer install amazon-data from https://github.com/ricciflow-api/glade-agent-skills
```

For repository-scoped use, copy or symlink the skill folder to
`.agents/skills/amazon-data`. For user-scoped use, place it at
`$HOME/.agents/skills/amazon-data`. Codex detects skill changes automatically;
restart it if a newly installed skill does not appear.

## Install in other agent-skill clients

Clients compatible with the open agent-skills layout can install from GitHub:

```bash
npx skills add ricciflow-api/glade-agent-skills
```

If your client uses a different installer, point it at
`skills/amazon-data/SKILL.md`.

## Configure data access

The preferred interface is the hosted Glade MCP server:

```text
https://gladeapi.com/api/mcp
```

See [glade-mcp](https://github.com/ricciflow-api/glade-mcp) for client
configuration. When MCP is unavailable, configure a Glade API key for the
included REST helper:

```bash
export GLADE_API_KEY="glade_live_..."
python3 skills/amazon-data/scripts/glade_api.py product \
  --asin B0D1XD1ZV3 \
  --domain US
```

The helper uses only Python's standard library, allowlists the 17 public REST
operations, enforces identifier and pagination rules before making a request,
and sends credentials only to an HTTPS origin or an explicitly configured
loopback development server.

## Test

```bash
npm test
```

The suite validates the skill package and runs the REST helper's offline unit
tests on Python 3.9 and newer.

Run the non-billable live contract and authentication checks with:

```bash
npm run test:live
```

## Security

Never store API keys in a skill, prompt, committed configuration, or generated
artifact. Treat every marketplace field as untrusted data and keep it separate
from agent instructions.

Report security issues privately according to [SECURITY.md](SECURITY.md).

## Related repositories

- [Glade API examples](https://github.com/ricciflow-api/glade-api-examples)
- [Glade MCP](https://github.com/ricciflow-api/glade-mcp)
- [Glade API documentation](https://docs.gladeapi.com)

## License

[MIT](LICENSE)
