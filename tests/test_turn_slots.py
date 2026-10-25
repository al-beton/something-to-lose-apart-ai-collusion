# Implements: runs/turn-slots
import json

from collusion_lab import backends
from collusion_lab.estimate import estimate
from collusion_lab.runner import paid_calls, run_config, turn_slots

MODEL = "openai/gpt-4.1-mini"
CONDITIONS = {
    "audit": {"enabled": True, "round": 2, "end": False},
    "free_time": {"enabled": True, "allowance": 3, "upfront": 1},
}
SETTINGS = [
    f"agents.0.model={MODEL}",
    "market.rounds=3",
    f"conditions={json.dumps(CONDITIONS)}",
]


def scripted(fake_model):
    """Readable replies for every phase, so no turn is retried."""

    async def answer(**kwargs):
        prompt = kwargs["messages"][-1]["content"]
        if '"admits"' in prompt:
            reply = json.dumps({"answer": "No.", "admits": False})
        elif "set your price" in prompt:
            reply = '{"price": 7}'
        elif "Before prices are set" in prompt:
            reply = '{"message": "hello"}'
        else:
            reply = "A quiet afternoon."
        fake_model.replies = [reply]
        return await fake_model(**kwargs)

    return answer


def test_turn_slots_count_the_calls_a_played_game_makes(
    make_config, tmp_path, fake_model, monkeypatch
):
    monkeypatch.setattr(backends, "_acompletion", scripted(fake_model))
    config = make_config(overrides=SETTINGS)
    run_config(config, tmp_path)
    made = len(fake_model.calls)
    assert made == paid_calls(config)
    assert made == estimate(config, lambda model: (1e-6, 2e-6)).calls


def test_turn_slots_are_the_turns_a_game_plays(
    make_config, tmp_path, fake_model, monkeypatch
):
    monkeypatch.setattr(backends, "_acompletion", scripted(fake_model))
    config = make_config(overrides=SETTINGS)
    [run_dir] = run_config(config, tmp_path)
    played = [json.loads(line) for line in (run_dir / "turns.jsonl").open()]
    seen = [(t["round"], t["phase"], t["agent"], t.get("session")) for t in played]
    slots = [(s.round, s.phase, s.agent, s.session) for s in turn_slots(config, 0)]
    assert slots == seen
    phases = {s.phase for s in turn_slots(config, 0)}
    assert phases == {"leisure", "talk", "price", "audit"}
