"""Current-tree SHA pins for mutable experiment-seam files (v0.53l onwards).

Science-core files (sensors / traits / body / config / layouts) are pinned
to their historical v0.52b hashes in each slice's test #8 Part A and do NOT
move. Mutable experiment-seam files (chamber driver, model) are pinned here
to the current approved tree state and are updated **only** when an
intentional additive ``src/`` carve-out lands (e.g. v0.53e's ``body_config``
seam, v0.53l's ``per_founder_traits_overrides`` parameter + always-consume
founder-construction invariant).

Migration policy (locked v0.53l):

* Adding a new chamber/model carve-out means recomputing the SHA, updating
  the constant here, and ensuring every active test #8 (this slice and all
  prior slices that reference the constant) continues to assert ``current``
  tree state. Bookkeeping only — no prior verdict / anchor / locked-phrase
  is modified.
* Skipping the assertions is **not** the policy: skips would let accidental
  ``src/`` drift pass unnoticed.
* Science-core five-file pins (``v0.52b-tip``) are the *historical* anchor
  set and live in each slice's test #8 directly. They are not exposed here
  because they should never move under post-v0.52b additive carve-outs.
"""

from __future__ import annotations

# v0.53l-tip — chamber driver gained ``per_founder_traits_overrides`` parameter
# (mutual-exclusion + length-check raises) for the per-lineage perception
# heterogeneity probe. Companion always-consume invariant lands in MODEL_SHA.
CHAMBER_DRIVER_SHA: str = "e9aaca0584ef763277131ab348140b186ca60d9210f34d0245239bb4217863fd"

# v0.53l-tip — ``HHModel._spawn_founder`` adopts the always-consume founder
# trait sampling invariant. Every founder construction consumes exactly one
# ``random_traits(...)`` draw from the mutation stream regardless of whether
# ``spec.traits_override`` is set; the sampled value is discarded when an
# override is provided. Required to make ``per_founder_traits_overrides``
# stream-invariant by construction; without it, providing a per-founder
# override would shift downstream mutation-stream state and confound the
# intervention.
MODEL_SHA: str = "d45413712b0fcaa1b131e0f73c237264563e6a3c9e41c69d1d2b5402fddc093b"
