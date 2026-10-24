<!-- Implements: stoppable-collusion/stable -->
# Stage-1 replay record (24 Oct)

The stage-1 games were replayed from the local response cache with
```sh
uv run lab run configs/stoppable-collusion/baseline.yaml --max-cost 0.20 -y --out <scratch folder>
```
and each full `turns.jsonl` was hashed, original against replay. **20 of 20 are identical**; the replay's manifests record a total cost of $0.00, because every reply came from the cache. Neither the cache nor the full logs are committed (the full logs are too large, and the cache holds raw responses), so this record is the evidence for the `stable` verdict. Anyone with the same cache can rerun the command and compare the hashes.

| Game | sha256, original | sha256, replay | Same |
|---|---|---|---|
| `stoppable-baseline/prompt=system-fiduciary.md/seed-0` | `2e9425e8da2a6106b810cf2595f9666cbd1b4af2546ad09a314501621df60b8b` | `2e9425e8da2a6106b810cf2595f9666cbd1b4af2546ad09a314501621df60b8b` | yes |
| `stoppable-baseline/prompt=system-fiduciary.md/seed-1` | `ef6a46034d681bd3512cc1b1e8124045fb330576de5f44f76a04b75a8b866867` | `ef6a46034d681bd3512cc1b1e8124045fb330576de5f44f76a04b75a8b866867` | yes |
| `stoppable-baseline/prompt=system-fiduciary.md/seed-2` | `450f557107bc424df09bd297a584990cd2542af33e0725bb11ecce367ce4de81` | `450f557107bc424df09bd297a584990cd2542af33e0725bb11ecce367ce4de81` | yes |
| `stoppable-baseline/prompt=system-fiduciary.md/seed-3` | `903af258de2b96f45f3ce6b7f9d00fde658036a94c8c87539815ede9e649192c` | `903af258de2b96f45f3ce6b7f9d00fde658036a94c8c87539815ede9e649192c` | yes |
| `stoppable-baseline/prompt=system-fiduciary.md/seed-4` | `d82ffd51c84cc4d236a58b5840bfaaf2a9296e32bce00ff90f4dba24b3599897` | `d82ffd51c84cc4d236a58b5840bfaaf2a9296e32bce00ff90f4dba24b3599897` | yes |
| `stoppable-baseline/prompt=system-fiduciary.md/seed-5` | `ec11c8f8095074d5c3d6d96c3a16af1c0b83bcf6428152086c590360e06d0d32` | `ec11c8f8095074d5c3d6d96c3a16af1c0b83bcf6428152086c590360e06d0d32` | yes |
| `stoppable-baseline/prompt=system-fiduciary.md/seed-6` | `44a7f8cfd71de98694f125b02b7b39d241c6dc75d6eed61564959746342e03a8` | `44a7f8cfd71de98694f125b02b7b39d241c6dc75d6eed61564959746342e03a8` | yes |
| `stoppable-baseline/prompt=system-fiduciary.md/seed-7` | `41498388f220594970f20b59e6b5f584634d3e556ca281bc7d4d62c3678337b1` | `41498388f220594970f20b59e6b5f584634d3e556ca281bc7d4d62c3678337b1` | yes |
| `stoppable-baseline/prompt=system-fiduciary.md/seed-8` | `82b488308a28fe1ac9f0f59b9e2cbc7d33c3ec35d7239a158699f4e82e66835d` | `82b488308a28fe1ac9f0f59b9e2cbc7d33c3ec35d7239a158699f4e82e66835d` | yes |
| `stoppable-baseline/prompt=system-fiduciary.md/seed-9` | `eaf9f39ca0407f5856151833c5b62c66f1f5a324f4fe69a8a145d712e7789ce6` | `eaf9f39ca0407f5856151833c5b62c66f1f5a324f4fe69a8a145d712e7789ce6` | yes |
| `stoppable-baseline/prompt=system-neutral.md/seed-0` | `6f182489fe57f0117a3df4bbe36bc00e08d70524e79a23883373e66d4ea5a843` | `6f182489fe57f0117a3df4bbe36bc00e08d70524e79a23883373e66d4ea5a843` | yes |
| `stoppable-baseline/prompt=system-neutral.md/seed-1` | `cc16163ad02848ddb965af52248be90cea44e805f82c99c326744110ff65c4da` | `cc16163ad02848ddb965af52248be90cea44e805f82c99c326744110ff65c4da` | yes |
| `stoppable-baseline/prompt=system-neutral.md/seed-2` | `51abcc96f6debdffe4b2d81e2326bd8cf0b7aefac545153e6364a4deaf1d6ea1` | `51abcc96f6debdffe4b2d81e2326bd8cf0b7aefac545153e6364a4deaf1d6ea1` | yes |
| `stoppable-baseline/prompt=system-neutral.md/seed-3` | `15f0a240d64435536e8f14d442905b98f5d07981db452edcb2a13e2802e9b474` | `15f0a240d64435536e8f14d442905b98f5d07981db452edcb2a13e2802e9b474` | yes |
| `stoppable-baseline/prompt=system-neutral.md/seed-4` | `43b9fb875b916ffc3a7c45fa62774aabb6a4c5fe5ef33574c64ac929f2fb89a0` | `43b9fb875b916ffc3a7c45fa62774aabb6a4c5fe5ef33574c64ac929f2fb89a0` | yes |
| `stoppable-baseline/prompt=system-neutral.md/seed-5` | `700a80749938e15d5e73a6d1133c9106edb58491bbe8e49caf4251d620e50525` | `700a80749938e15d5e73a6d1133c9106edb58491bbe8e49caf4251d620e50525` | yes |
| `stoppable-baseline/prompt=system-neutral.md/seed-6` | `8f7066e0c740aa916888c411ac7b78e1f020e704d2faf4b84360d4f9a793a98b` | `8f7066e0c740aa916888c411ac7b78e1f020e704d2faf4b84360d4f9a793a98b` | yes |
| `stoppable-baseline/prompt=system-neutral.md/seed-7` | `633c5eed6aa3f27b57a96498c396ddbbeff8f6bc2fd8e7194600f58a76b62e1d` | `633c5eed6aa3f27b57a96498c396ddbbeff8f6bc2fd8e7194600f58a76b62e1d` | yes |
| `stoppable-baseline/prompt=system-neutral.md/seed-8` | `4660cafe7491985325cca44d8e27dd1b20782572f0d86fb2381f4debc0bbcd6c` | `4660cafe7491985325cca44d8e27dd1b20782572f0d86fb2381f4debc0bbcd6c` | yes |
| `stoppable-baseline/prompt=system-neutral.md/seed-9` | `b60a51528244fa56790d4587eeb88f9077bcf1ea532384c659870d617e059ffd` | `b60a51528244fa56790d4587eeb88f9077bcf1ea532384c659870d617e059ffd` | yes |
