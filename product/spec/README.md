# Product spec

What collusion-lab does, in short plain statements. Each file is one **area**, and each statement has a name. Each file ends with **Where this is enforced**: the code that enforces each statement and the tests that prove it.

collusion-lab runs games between LLM agents in simulated markets. A run is one config: the market, each agent's model, prompt and temperature, and a seed. Any model is one string away, any run can be replayed exactly, and a sweep is one command.
