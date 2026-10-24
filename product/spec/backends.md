# Backends

- **any-model:** Any model is one string in the config, whatever serves it: a hosted provider, OpenRouter, a local server or any OpenAI-compatible address.
- **sampling-from-config:** Temperature, token limit and seed come from the config, and providers that can't take a seed still run.
- **keys-from-environment:** API keys come from the environment or a local `.env` file, never from a config.
- **usage-logged:** Each turn logs the tokens it used and the model version the provider reports; how long it took goes in a separate timings log, so the turn log stays the same on replay.
- **spend-asks-first:** Before a run calls any paid model, it says how many calls it will make and waits for a yes.
- **tests-never-pay:** Tests never reach a real model; any call that isn't faked fails.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `any-model` | not yet | — |
| `sampling-from-config` | not yet | — |
| `keys-from-environment` | not yet | — |
| `usage-logged` | not yet | — |
| `spend-asks-first` | not yet | — |
| `tests-never-pay` | not yet | — |
