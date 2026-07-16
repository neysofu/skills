---
name: openrouter-api-auth
description: Find the OpenRouter API key for local API calls. Use when an agent needs to interact with OpenRouter and needs credentials.
---

Never put the OpenRouter API key in prompts or anywhere else except this file:

```text
~/.config/openrouter/api_key
```

When an OpenRouter API key is needed, read it from that file without exposing it. Do not look for it anywhere else.

If the key is expected but the file is missing, unreadable, or empty, stop and report the error to the end user in the final response.
