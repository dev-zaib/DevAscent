# P1-01: Strip Unused Gateway Platforms + Tools

**Status:** ⬜ todo
**Phase:** 1 — Foundation
**Depends on:** None
**Blocks:** P1-02

## Goal
Remove all gateway platform adapters and tools that are irrelevant to the DevAscent assessment platform. Keep only what we need: webhook, api_server, and the core agent infrastructure.

## AC (Acceptance Criteria)
- [ ] All messaging platform adapters removed from `gateway/platforms/`
- [ ] Gateway `run.py` imports cleaned up — no broken references to removed adapters
- [ ] Browser tools removed (`browser_navigate`, `browser_snapshot`, etc.)
- [ ] Voice/TTS tools removed
- [ ] Image generation tools removed
- [ ] `docker-compose.yml` updated — single assessment service
- [ ] `pyproject.toml` — optional deps for removed platforms cleaned
- [ ] `scripts/run_tests.sh` passes (only remaining tests)
- [ ] AGENTS.md updated — removed platform/voice/browser sections no longer relevant

## Files to Remove

### Gateway Platforms (keep: webhook, api_server)
```
gateway/platforms/telegram.py
gateway/platforms/discord.py
gateway/platforms/slack.py
gateway/platforms/whatsapp.py
gateway/platforms/signal.py
gateway/platforms/matrix/
gateway/platforms/mattermost.py
gateway/platforms/email.py
gateway/platforms/sms.py
gateway/platforms/dingtalk.py
gateway/platforms/wecom/
gateway/platforms/weixin.py
gateway/platforms/feishu.py
gateway/platforms/qqbot.py
gateway/platforms/bluebubbles.py
gateway/platforms/yuanbao.py
gateway/platforms/homeassistant.py
gateway/platforms/teams.py
gateway/platforms/google_chat.py
```

### Tools (remove browser, voice, image gen, messaging-specific)
```
tools/browser_tool.py
tools/browser_navigate_tool.py
tools/browser_snapshot_tool.py
tools/browser_*.py  # all browser variants
tools/voice_tool.py
tools/stt_tool.py
tools/tts_tool.py
tools/image_gen_tool.py
tools/send_message_tool.py
tools/homeassistant_*.py
tools/spotify_*.py
tools/kanban_tools.py
```

### Optional skills (remove non-assessment)
```
optional-skills/autonomous-ai-agents/
optional-skills/blockchain/
optional-skills/communication/
optional-skills/creative/
optional-skills/email/
optional-skills/health/
optional-skills/mlops/
optional-skills/productivity/
optional-skills/research/
optional-skills/web-development/
```

### Docker/Desktop (remove)
```
apps/desktop/
ui-tui/
tui_gateway/
docker/s6-rc.d/user/
docker/s6-rc.d/main-hermes/
```

## Files to Modify

### `pyproject.toml`
- Remove `[project.optional-dependencies]` entries for: `messaging`, `slack`, `matrix`, `sms`, `teams`, `dingtalk`, `feishu`, `wecom`, `voice`, `tts-premium`, `homeassistant`, `computer-use`, `termux`
- Remove `edge-tts`, `browser` deps from core if present
- Remove `[all]` extra (we don't need it)
- Remove `gateway` from `packages.find` if no longer needed
- Remove `devascent_cli` (CLI not needed for web-only platform)
- Remove `locales` data-files (i18n not needed for MVP)

### `package.json`
- Remove `apps/desktop`, `ui-tui` from workspaces
- Update repo URL to `dev-zaib/DevAscent`

### `docker-compose.yml`
- Single service: `assessment` (web + worker)
- Remove `gateway` + `dashboard` services
- Add PostgreSQL + Redis services

### `.env.example`
- Strip to assessment-only variables:
  - Keep: LLM provider keys (OpenAI, Anthropic)
  - Add: `DATABASE_URL`, `REDIS_URL`
  - Remove: Telegram, Discord, Slack, WhatsApp, Signal, Email, SMS, Browser, Voice, TTS, all platform keys

### `AGENTS.md`
- Remove sections: Gateway platforms, TUI, Desktop, Browser, Voice/TTS, Kanban
- Keep: Agent loop, tools registry, plugins, skills, testing

## Hermes Convention Checks
- [x] No DEVASCENT_ env var additions for non-secret config
- [x] Keep provider system (`providers/`) — needed for LLM calls
- [x] Keep plugin system — we'll add assessment as a plugin
- [x] Keep `scripts/run_tests.sh` test infrastructure
- [x] Exact dependency pins maintained in pyproject.toml