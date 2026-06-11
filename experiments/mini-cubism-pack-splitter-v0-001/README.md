# Mini Cubism Pack Splitter v0 001

Status: `LAYERD_ACTUAL_RUNTIME_PASS_REVISE_MASK_PENDING_SAM2`

This experiment is reserved for the pack-based Mini Cubism splitter path:

```text
clean base mannequin
  + hair_pack
  + outfit_pack
  + accessory_pack
  + keypose_asset_pack
```

The purpose is to replace the single-image 70+ decomposition attempt with pack-level decomposition, Hugging Face model probes, QA contact sheets, and promotion gates.

Current base policy:

```text
neutral two-piece swimsuit / rig underlayer
  - chest cover
  - pelvis cover
  - abdomen visible as skin
```

The base must support belly-visible outfits, crop tops, and open jacket variants. One-piece bodysuit/swimsuit bases are not the default.

Authoritative plan:

```text
docs/ref/MINI-CUBISM-PACK-SPLITTER-v0-PLAN.md
```

Real hair, outfit, accessory, and keypose pack assets are now connected as full-canvas alpha PNG sources. Local adapter probe QA passed on these real assets. Actual LayerD BiRefNet inference also ran on all 4 packs; hair/outfit are candidate masks, while accessory/keypose masks are broad and need SAM2 ROI refinement. Existing `See-through 70+ custom split v2` evidence remains a negative gate and must not be overwritten.
