<!-- Implements: specs-and-docs/folder-guides -->
# Tests

Every test runs offline and free: `make test`. Agents are scripted or replay fixed replies, so no model is called. A test is named after the spec statement it proves (`test_<statement>_...`), and each spec file's "Where this is enforced" table lists them. `data/` holds fixtures; `test_e2e.py` plays a scripted sweep through summary and report.
