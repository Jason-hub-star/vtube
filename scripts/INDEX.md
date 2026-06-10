# scripts/ 인덱스

Updated: 2026-06-10 · 총 272개 · `python3 scripts/build_scripts_index.py`로 재생성

새 스크립트를 만들기 전에 이 인덱스에서 기존 것을 먼저 찾는다.
코드 규칙: `docs/ref/AUTORIG-PIPELINE-V1.md`의 '코드 규칙' 절 (lib 사용 의무, 캐릭터 하드코딩 금지, 500줄 상한).

## lib — 공유 라이브러리 — 새 코드는 여기서 import (복붙 금지) (5)

| 파일 | LOC | 설명 |
|---|---:|---|
| `lib/__init__.py` | 13 | Vtube 공유 라이브러리. |
| `lib/vtube_image.py` | 113 | 이미지 공통 유틸: 알파크롭 썸네일, 컨택트시트, 픽셀 diff. (build_contact_sheet 26벌 복붙의 단일 원본) |
| `lib/vtube_io.py` | 41 | 경로/JSON 입출력 공통 유틸. (기존 258개 스크립트에 rel 151벌, load_json 145벌이 복붙되어 있던 것의 단일 원본) |
| `lib/vtube_proc.py` | 29 | 프로세스/포트 공통 유틸. (wait_for_server 17벌 복붙의 단일 원본) |
| `lib/vtube_server.py` | 60 | 로컬 HTTP 서버 공통 베이스. (ThreadingHTTPServer 보일러플레이트 13벌 복붙의 단일 원본) |

## autorig — AUTORIG 파이프라인·관제탑·자산 인덱스 (현행) (9)

| 파일 | LOC | 설명 |
|---|---:|---|
| `autorig_events.py` | 228 | AUTORIG 이벤트 로그(JSONL) 공유 라이브러리. |
| `build_asset_dashboard.py` | 237 | Vtube 자산 대시보드 생성기. |
| `build_autorig_current_candidates_002.py` | 119 | AUTORIG current-candidates manifest for cubism-v2-new-character-002. |
| `build_autorig_full_assembly.py` | 127 | 모든 시트의 정규화 레이어를 모아 전신 조립 합성을 만든다 (검수 단위 규칙). |
| `build_autorig_template_spec.py` | 200 | AUTORIG-TEMPLATE-SPEC-001: 64-part를 고정 슬롯 시트에 매핑하는 템플릿 스펙 생성. |
| `build_scripts_index.py` | 94 | scripts/INDEX.md 자동 생성 — 258개 스크립트를 카테고리·설명·LOC로 색인한다. |
| `run_autorig_control_tower.py` | 262 | AUTORIG 관제탑 서버 — runs/<run_id>/events.jsonl을 읽어 대시보드에 공급한다. |
| `run_autorig_sheet_pilot.py` | 300 | AUTORIG 슬롯 시트 파일럿: 시트 1장을 생성→점유율 QA→결정론적 추출→배치→조립 합성. |
| `simulate_autorig_run.py` | 153 | AUTORIG 가짜 런 시뮬레이터 — 관제탑 개발/스모크용. |

## webcam-drive — 트래킹·웹캠 드라이브 (T0–T3) (6)

| 파일 | LOC | 설명 |
|---|---:|---|
| `build_face_tracking_to_cubism_parameter_map.py` ⚠️ | 536 | Build a face-tracking to Cubism parameter mapping spec for the v2 model. |
| `run_face_tracking_synthetic_parameter_smoke.py` | 354 | Run T0 synthetic face-tracking to Cubism parameter conversion smoke. |
| `run_face_tracking_webcam_probe_server.py` | 333 | Serve a local MediaPipe webcam probe and save T1 face-tracking reports. |
| `run_live2d_webcam_parameter_drive.py` | 411 | Drive a Live2D Web model with the saved T1 webcam Cubism parameter stream. |
| `run_mini_cubism_webcam_drive.py` | 420 | T3: 웹캠/재생 트래킹 스트림으로 Mini Cubism 런타임을 구동하는 드라이브 서버. |
| `run_mini_cubism_webcam_drive_smoke.py` | 279 | T3-a/b 스모크: 합성 파라미터 + 저장된 T1 스트림 재생으로 Mini Cubism 드라이브를 검증한다. |

## servers-editors — 로컬 서버·에디터·플레이어 (9)

| 파일 | LOC | 설명 |
|---|---:|---|
| `run_cubism_v2_keypose_anchor_editor_002.py` ⚠️ | 501 | Serve a manual eye/mouth keypose alignment editor for character 002. |
| `run_cubism_v2_material_review_server.py` ⚠️ | 579 | Serve and save human review for the Cubism v2 material contact sheet. |
| `run_cubism_v2_semantic_anchor_editor.py` ⚠️ | 684 | Serve a G1.6 semantic anchor editor for Cubism v2 parts. |
| `run_live2d_all57_model_carousel_player.py` | 87 | Build and run the all57 Live2D model carousel player. |
| `run_live2d_model_carousel_player.py` | 77 | Build and run the strong20 Live2D model carousel player. |
| `run_v19_eye_detail_anchor_editor_002.py` | 237 | Serve a small manual anchor editor for Character 002 v19 generated eye detail. |
| `run_v22_b4_b5_anchor_editor_002.py` | 337 | Serve a drag/zoom anchor editor for v22 B4/B5 correction targets. |
| `run_v22_b4_b5_focused_owner_review_server_002.py` | 392 | Serve a focused owner-review UI for v22 B4/B5 primary decisions. |
| `run_v22_g6_hairfront_anchor_editor_002.py` | 431 | Serve a G6 HairFront anchor editor for Character 002 v22. |

## validators-qa — 검증·QA·스모크 (21)

| 파일 | LOC | 설명 |
|---|---:|---|
| `run_control_tower_browser_smoke.py` | 214 | 관제탑 브라우저 스모크 (Playwright headless). |
| `run_live2d_all57_motion_playback_qa.py` | 378 | Run all57 Live2D representative-motion playback QA and build a matrix report. |
| `run_live2d_parameter_single_sweep.py` | 454 | Run single-parameter min/max sweeps for strong20 Live2D reference models. |
| `run_live2d_runtime_probe_capture.py` | 332 | Capture neutral/motion/extreme screenshots from the generated Live2D probe sandbox. |
| `run_mini_cubism_face_qa.py` | 316 | Capture face-focused Mini Cubism QA evidence. |
| `run_mini_cubism_hf_pack_probe.py` | 283 | Run Mini Cubism pack-splitter-v0 model probe adapters and contact sheets. |
| `run_mini_cubism_motion_sweep.py` | 337 | Capture animated Mini Cubism Physics v0.3 motion sweeps. |
| `run_mini_cubism_pose_sweep.py` | 448 | Capture and score Mini Cubism preview poses automatically. |
| `run_misc_pack_model_probes.py` | 193 | Probe miscellaneous HF vision models for Mini Cubism pack splitter. |
| `score_mini_cubism_physics.py` | 213 | Score Mini Cubism Physics v0.3 motion evidence. |
| `smoke_test_control_tower.py` | 241 | 관제탑 다각도 스모크 (파이썬 측). |
| `validate_cubism_psd_inputs.py` | 8 | CLI wrapper for validating the Cubism material pack. |
| `validate_cubism_v2_keypose_pngs.py` | 189 | Validate clean-socket/keypose PNG outputs for the current Cubism v2 material pack. |
| `validate_cubism_v2_material_assets.py` | 165 | Validate the Cubism v2 material asset draft. |
| `validate_mini_cubism_dedicated_part_spec.py` | 97 | Validate the Mini Cubism dedicated model part spec manifest. |
| `validate_mini_cubism_eye_modes.py` ⚠️ | 635 | Validate Mini Cubism eye controls with ROI leakage checks. |
| `validate_mini_cubism_pack_splitter_v0.py` | 157 | Validate Mini Cubism pack-splitter-v0 bootstrap/probe outputs. |
| `validate_mini_cubism_project.py` | 151 | Validate a Mini Cubism v0 project contract. |
| `validate_mini_cubism_targeted_split.py` | 165 | Validate Mini Cubism targeted split candidate manifest. |
| `validate_review_app.py` | 216 | Validate the part-purity review app data contracts. |
| `validate_seethrough_70_custom_split_v2.py` | 387 | QA-first validator for See-through 70+ custom split v2 candidates. |

## live2d-reference — 공식 레퍼런스 분석 (완료된 베이스라인) (21)

| 파일 | LOC | 설명 |
|---|---:|---|
| `analyze_reference_model_catalog.py` ⚠️ | 679 | Batch-analyze reference Live2D model structure from a catalog. |
| `build_cmo3_structure_positive_fixture.mjs` | 85 | (node) |
| `build_cubism_success_pattern_spec.py` | 390 | Build the Cubism-first success pattern spec from measured official baselines. |
| `build_live2d_all57_model_carousel_player.py` | 393 | Build an all57 Live2D carousel page with runtime/unavailable states. |
| `build_live2d_all57_production_design_spec.py` ⚠️ | 1468 | Build Cubism v2 production design tables from the 57 Live2D references. |
| `build_live2d_all57_render_manifest.py` | 173 | Build an all57 Live2D player manifest from the official combined catalog. |
| `build_live2d_cmo3_deformer_hierarchy_table.py` | 348 | Build detailed deformer hierarchy tables for all FULL_STRUCTURE CMO3 references. |
| `build_live2d_deep_reference_motion_analysis.py` ⚠️ | 821 | Build deeper Live2D reference motion and rig pattern analysis. |
| `build_live2d_model_carousel_player.py` | 289 | Build a Korean arrow-key carousel page for the strong20 Live2D sandbox. |
| `build_live2d_official_sample_profiles.py` ⚠️ | 530 | Build concise official-learning profiles for Live2D sample models. |
| `build_live2d_owned_model_motion_readiness.py` | 175 | Build a motion-readiness report for owned/collected official Live2D models. |
| `build_live2d_part_success_pattern_spec.py` | 443 | Summarize Live2D part success patterns and Cubism v2 tier specs. |
| `build_live2d_runtime_metadata_extras.py` ⚠️ | 547 | Extract auxiliary Live2D runtime metadata from the official reference corpus. |
| `build_live2d_runtime_probe_sandbox.py` ⚠️ | 524 | Build an isolated Cubism Web Samples probe sandbox for selected models. |
| `build_live2d_strong_model_render_manifest.py` | 220 | Build render manifests for strong official Live2D reference models. |
| `build_reference_rig_pattern_baseline.py` | 259 | Build a success-pattern baseline from official profiles and measured reports. |
| `compare_cmo3_structure_reports.py` | 218 | Compare two CMO3 structure reports. |
| `inspect_cmo3_structure.mjs` ⚠️ | 791 | (node) |
| `prepare_official_live2d_github_samples.py` | 378 | Fetch official Live2D GitHub sample resources and build runtime catalogs. |
| `prepare_official_live2d_samples.py` | 377 | Safely extract official Live2D sample zips and build a model catalog. |
| `test_live2d_model_motion_and_view.py` | 306 | Test Live2D model runtime readiness and view-clipping risk. |

## mini-cubism — Mini Cubism 자체 런타임·리그 빌더 (36)

| 파일 | LOC | 설명 |
|---|---:|---|
| `build_mini_cubism_all_mouth_enabled_packet_002.py` | 311 | Capture Character 002 v9 all-mouth-enabled diagnostic frames. |
| `build_mini_cubism_dedicated_model_v1.py` ⚠️ | 626 | Build a Mini Cubism dedicated model v1 procedural rig seed. |
| `build_mini_cubism_diagnostic_from_keypose_pack_002.py` | 262 | Build a Mini Cubism diagnostic project from character-002 keypose layers. |
| `build_mini_cubism_existing_mouth_open_packet_002.py` | 412 | Capture existing-mouth-only MouthOpenY evidence for Character 002 Mini Cubism. |
| `build_mini_cubism_eye_open_027_packet_002.py` | 472 | Capture the Character 002 EyeOpen 0.27 Mini Cubism success-pattern packet. |
| `build_mini_cubism_face_base_clean_v1.py` | 470 | Build a Mini Cubism candidate with baked eye pixels removed from face_base. |
| `build_mini_cubism_face_keypose_pack_v1.py` | 203 | Build separated eye and mouth keypose layers for Mini Cubism Hair+Face Motion v1. |
| `build_mini_cubism_face_v1.py` | 366 | Build a face-focused Mini Cubism candidate from the targeted project. |
| `build_mini_cubism_hair_face_project_v1.py` | 415 | Build Mini Cubism Hair+Face Motion v1 project from base, hair split, and keypose packs. |
| `build_mini_cubism_hair_fit_v1.py` | 144 | Fit the BiRefNet_HR hair pack to the clean base mannequin for Hair+Face Motion v1. |
| `build_mini_cubism_hair_split_v1.py` | 189 | Build local hair split parts for Mini Cubism Hair+Face Motion v1. |
| `build_mini_cubism_motion_review_packet.py` | 198 | Build the Mini Cubism Physics v0.3 motion review packet. |
| `build_mini_cubism_physics_v0_3.py` | 340 | Build the Mini Cubism Physics v0.3 project from the v0.1 best candidate. |
| `build_mini_cubism_pose_sweep_contact_sheet.py` | 97 | Build a contact sheet from a Mini Cubism pose sweep report. |
| `build_mini_cubism_project_from_cubism_v2_material_pack.py` | 400 | Build a Mini Cubism preview project from the Cubism v2 material pack. |
| `build_mini_cubism_project_from_seethrough70_v2.py` | 182 | Promote See-through 70+ v2 candidates to Mini Cubism only after QA PASS. |
| `build_mini_cubism_project_from_targeted_split.py` | 187 | Build a Mini Cubism project from targeted split candidate layers. |
| `build_mini_cubism_review_packet.py` | 181 | Build a visual review packet for Mini Cubism auto-authoring runs. |
| `build_mini_cubism_targeted_split_v1.py` | 409 | Expand coarse See-through layers into Mini Cubism dedicated part candidates. |
| `build_mini_cubism_v0.py` | 414 | Build a Vtube-native Mini Cubism v0 project from accepted Cubism parts. |
| `build_mini_cubism_v10_generated_mouth_eye_clamp_preview_002.py` | 235 | Build Character 002 generated-mouth preview with EyeOpen min clamp. |
| `build_mini_cubism_v13_scale_tune_preview_002.py` | 212 | Build Character 002 v13 preview by slightly reducing v12 eye and mouth scale. |
| `build_mini_cubism_v14_eye_detail_inbetween_preview_002.py` | 431 | Build Character 002 v14 eye-detail/in-between diagnostic preview from v13. |
| `build_mini_cubism_v14_eye_detail_review_packet_002.py` | 449 | Capture Character 002 v14 eye-detail/in-between review packet. |
| `build_mini_cubism_v15_eye_nose_position_preview_002.py` | 288 | Build Character 002 v15 by fixing v14 eyeball cohesion, eye position, and nose visibility. |
| `build_mini_cubism_v16_whole_eyeball_preview_002.py` | 143 | Build Character 002 v16 by moving the full eyeball group on EyeBall X/Y. |
| `build_mini_cubism_v17_clean_white_full_iris_preview_002.py` | 298 | Build Character 002 v17 with cleaner fixed eye white and fuller moving iris assets. |
| `build_mini_cubism_v18_clean_white_center_iris_preview_002.py` | 263 | Build Character 002 v18 with fixed white and centered iris-only movement. |
| `build_mini_cubism_v19_generated_eye_preview_002.py` | 217 | Build Character 002 v19 by replacing v15 eye assets with generated clean eye materials. |
| `build_mini_cubism_v20_manual_eye_anchor_preview_002.py` | 190 | Build Character 002 v20 by applying saved manual eye-detail anchors from v19. |
| `build_mini_cubism_v20_rig_readiness_report_002.py` | 223 | Build a v20 rig-readiness and v21 scope report for Character 002. |
| `build_mini_cubism_v21_supported_rig_smoke_preview_002.py` | 107 | Build Character 002 v21 supported-control Mini Cubism rig smoke from v20. |
| `build_mini_cubism_v7_smooth_mouth_preview_002.py` | 125 | Build a v7 Mini Cubism preview with smooth mouth and unsupported sliders removed. |
| `build_mini_cubism_v8_existing_mouth_tuned_preview_002.py` | 132 | Build a v8 Mini Cubism preview tuned for existing generated mouth assets only. |
| `build_mini_cubism_v9_all_mouth_enabled_preview_002.py` | 226 | Build a Character 002 Mini Cubism preview with all existing mouth assets enabled. |
| `setup_mini_cubism_dedicated_layer_inputs.py` | 182 | Prepare Mini Cubism dedicated model v1 canonical and See-through inputs. |

## seethrough — 레이어 분해 (See-through/SAM2) (10)

| 파일 | LOC | 설명 |
|---|---:|---|
| `build_seethrough_70_custom_split_v2.py` | 257 | Build See-through 70+ custom split v2 candidates, then run QA gate. |
| `build_seethrough_psd_candidate.py` | 292 | Build a gated PSD candidate from human-approved See-through layers. |
| `normalize_seethrough_outputs.py` | 322 | Normalize ComfyUI-See-through layer outputs into Vtube review candidates. |
| `patch_comfyui_seethrough_mps.py` | 111 | Apply local Apple Silicon MPS compatibility patches to ComfyUI-See-through. |
| `reskin_seethrough_layers.py` | 101 | See-through 레이어 재스킨: 모양(알파)은 분해 결과, 픽셀은 원본 2048에서 가져온다. |
| `run_comfyui_seethrough_prompt.py` | 277 | Queue the Vtube See-through workflow through ComfyUI's HTTP API. |
| `run_layerd_birefnet_pack_inference.py` | 234 | Run actual LayerD BiRefNet HF inference on Mini Cubism pack sources. |
| `run_sam2_roi_pack_refinement.py` | 278 | Run SAM2 ROI refinement for Mini Cubism pack source targets. |
| `setup_comfyui_seethrough_mac.py` | 355 | Prepare and probe a Mac ComfyUI + ComfyUI-See-through experiment. |
| `watch_seethrough_to_events.py` | 95 | See-through 분해 진행을 관제탑 이벤트로 중계하는 브리지. |

## character-002 — character-002 종속 (대부분 일회용 — 재사용 전 AUTORIG 이식 검토) (125)

| 파일 | LOC | 설명 |
|---|---:|---|
| `apply_cubism_v2_part_localization_template.py` | 234 | Apply part_localization_template.json to split current candidate layers. |
| `build_cubism_v2_64part_candidate_manifest_002.py` | 371 | Build the v22 64-part candidate manifest from B1-B5 evidence. |
| `build_cubism_v2_64part_corrected_b4_b5_manifest_002.py` | 330 | Build a v22 64-part manifest candidate with corrected B4 and provisional B5 layers. |
| `build_cubism_v2_64part_g4_torso_selected_manifest_002.py` | 192 | Build a v22 64-part manifest variant with generated G4 torso_base selected. |
| `build_cubism_v2_64part_generation_input_packet_002.py` | 368 | Build the v22 image-generation input packet for character 002. |
| `build_cubism_v2_64part_generation_spec_002.py` ⚠️ | 581 | Build the v22 64-part generation spec for character 002. |
| `build_cubism_v2_64part_p0_torso_v2_manifest_002.py` | 157 | Build a v22 64-part manifest variant with the P0 torso v2 candidate. |
| `build_cubism_v2_anchor_clean_combined_candidate.py` | 117 | Combine anchor-position repair layers with clean-neutral opacity policy. |
| `build_cubism_v2_anchor_masked_clean_candidate.py` | 226 | Build an anchor-position + clean-neutral candidate without rectangular crops. |
| `build_cubism_v2_anchor_position_repair_candidate.py` | 246 | Build a visual candidate that trusts saved manual anchors for small parts. |
| `build_cubism_v2_b1_clean_base_layer_pack_002.py` | 383 | Build v22 B1 clean-base/underpaint full-canvas RGBA candidates. |
| `build_cubism_v2_b1_clean_base_review_002.py` | 211 | Review the v22 B1 clean-base raw candidate for character 002. |
| `build_cubism_v2_b1_visual_qa_002.py` | 120 | Record Codex visual QA for the v22 B1 clean-base layer pack. |
| `build_cubism_v2_b2_eye_layer_pack_002.py` | 392 | Extract v22 B2 eye-pack full-canvas RGBA candidates from the new raw sheet. |
| `build_cubism_v2_b2_eye_pack_review_002.py` | 245 | Review the v22 B2 newly generated eye-pack raw candidate. |
| `build_cubism_v2_b2_overlay_qa_002.py` | 205 | Record overlay QA for v22 B2 eye candidates on the B1 clean base. |
| `build_cubism_v2_b3_mouth_layer_pack_002.py` | 294 | Extract v22 B3 mouth-pack full-canvas RGBA candidates from the new raw sheet. |
| `build_cubism_v2_b3_mouth_layer_pack_revision_v1_002.py` | 301 | Build a v22 B3 mouth extraction revision from coherent mouth-state crops. |
| `build_cubism_v2_b3_mouth_pack_review_002.py` | 251 | Review the v22 B3 newly generated mouth-pack raw candidate. |
| `build_cubism_v2_b3_overlay_qa_002.py` | 179 | Record overlay QA for v22 B3 mouth candidates on the B1 clean base. |
| `build_cubism_v2_b3_revision_v1_overlay_qa_002.py` | 124 | Record overlay QA for v22 B3 mouth extraction revision v1. |
| `build_cubism_v2_b4_b5_anchor_corrected_candidate_002.py` | 305 | Build B4/B5 corrected layer candidates from saved anchor overrides. |
| `build_cubism_v2_b4_b5_anchor_correction_readiness_002.py` | 244 | Build a G6 readiness packet for v22 B4/B5 anchor correction. |
| `build_cubism_v2_b4_b5_auto_anchor_draft_002.py` | 152 | Create a conservative automatic B4/B5 anchor draft. |
| `build_cubism_v2_b4_b5_auto_draft_overlay_qa_002.py` | 168 | Build conservative overlay QA for the v22 B4/B5 auto-draft corrected candidate. |
| `build_cubism_v2_b4_b5_auto_draft_review_triage_002.py` | 161 | Triage the B4/B5 auto-draft overlay into review vs re-extraction buckets. |
| `build_cubism_v2_b4_b5_codex_provisional_decisions_002.py` | 165 | Seed v22 B4/B5 focused decisions from current success patterns. |
| `build_cubism_v2_b4_b5_focused_owner_review_packet_002.py` | 304 | Build the focused owner review packet for v22 B4/B5 blockers. |
| `build_cubism_v2_b4_b5_owner_decision_route_plan_002.py` | 274 | Build a route plan from v22 B4/B5 focused owner decisions. |
| `build_cubism_v2_b4_hair_focused_review_002.py` | 342 | Build a focused B4 hair review packet for the v22 64-part pipeline. |
| `build_cubism_v2_b4_hair_layer_pack_002.py` | 347 | Extract v22 B4 hair-pack full-canvas RGBA candidates from the new raw sheet. |
| `build_cubism_v2_b4_hair_pack_review_002.py` | 271 | Review the v22 B4 newly generated hair-pack raw candidate. |
| `build_cubism_v2_b4_overlay_qa_002.py` | 123 | Run conservative overlay QA for the v22 B4 hair layer-pack candidate. |
| `build_cubism_v2_b5_body_blocker_draw_order_review_002.py` | 294 | Build a draw-order-aware review packet for the three B5 hard blockers. |
| `build_cubism_v2_b5_body_clothing_layer_pack_002.py` | 394 | Extract v22 B5 body/clothing full-canvas RGBA candidates from the new raw sheet. |
| `build_cubism_v2_b5_body_clothing_pack_review_002.py` | 272 | Review the v22 B5 newly generated body/clothing-pack raw candidate. |
| `build_cubism_v2_b5_overlay_qa_002.py` | 123 | Run conservative overlay QA for the v22 B5 body/clothing layer-pack candidate. |
| `build_cubism_v2_b5_provisional_minipass_candidate_002.py` | 330 | Build a B5 provisional mini-pass candidate from the route packet. |
| `build_cubism_v2_b5_provisional_minipass_input_packet_002.py` | 168 | Build the B5 provisional mini-pass input packet from the Codex route plan. |
| `build_cubism_v2_b5_provisional_minipass_overlay_qa_002.py` | 207 | Conservative overlay QA for the B5 provisional mini-pass candidate. |
| `build_cubism_v2_b5_refined_mask_v1_002.py` | 337 | Build a B5 refined-mask v1 candidate from the auto-draft corrected layers. |
| `build_cubism_v2_b5_refined_mask_v1_overlay_qa_002.py` | 145 | Record conservative visual QA for B5 refined-mask v1. |
| `build_cubism_v2_b5_refined_mask_v2_002.py` | 310 | Build B5 refined-mask v2 for the six remaining focused revise parts. |
| `build_cubism_v2_b5_refined_mask_v2_overlay_qa_002.py` | 141 | Record conservative visual QA for B5 refined-mask v2. |
| `build_cubism_v2_character_prompt_template.py` | 377 | Build Cubism v2 character prompt templates from production design evidence. |
| `build_cubism_v2_clean_neutral_opacity_candidate.py` | 125 | Build a Mini Cubism candidate that hides helper/underpaint patches at neutral. |
| `build_cubism_v2_clean_socket_keypose_spec.py` | 323 | Write the clean-socket/keypose requirements and Imagen prompt plan. |
| `build_cubism_v2_corrected_b4_b5_codex_visual_triage_002.py` | 228 | Build Codex provisional visual triage for corrected v22 B4/B5 layers. |
| `build_cubism_v2_corrected_b4_b5_manifest_overlay_qa_002.py` | 209 | Build overlay QA for the corrected B4/B5 manifest candidate. |
| `build_cubism_v2_existing_mouth_review_packet_002.py` | 263 | Build a review packet from existing generated Character 002 mouth PNGs only. |
| `build_cubism_v2_feature_mask_clean_bases_002.py` | 217 | Build layer-alpha seed clean-base candidates for character-002. |
| `build_cubism_v2_flattened_canonical_debug_candidate.py` | 152 | Build a visual-only debug candidate with a flattened canonical overlay. |
| `build_cubism_v2_g0_existing_source_review_002.py` | 200 | Build the v22 G0 review result for character 002's existing source. |
| `build_cubism_v2_g1_material_plan.py` | 418 | Build the Cubism v2 G1 material planning packet. |
| `build_cubism_v2_g1_taxonomy_review.py` | 302 | Build G1 part-taxonomy feasibility evidence for the selected Cubism v2 character. |
| `build_cubism_v2_g2_g5_material_qa_prep_packet_002.py` | 164 | Build blocked G2-G5 material QA prep packet for character 002 v22. |
| `build_cubism_v2_g2_layer_manifest_technical_qa_002.py` | 274 | Run G2 layer-manifest technical QA for character 002 v22. |
| `build_cubism_v2_g3_b4_b5_blocker_reduction_packet_002.py` | 259 | Build a G3 B4/B5 blocker-reduction packet for character 002 v22. |
| `build_cubism_v2_g3_combined_context_overlay_review_002.py` | 287 | Build a combined G3 context overlay after P0/P1A blocker reduction. |
| `build_cubism_v2_g3_p0_torso_minipass_v2_002.py` | 351 | Build a focused P0 torso minipass v2 candidate for v22 G3 review. |
| `build_cubism_v2_g3_p1_b4_secondary_hair_reduction_packet_002.py` | 257 | Reduce P1 B4 secondary-hair blockers into focused follow-up routes. |
| `build_cubism_v2_g3_p1a_b4_back_strand_anchor_mask_probe_002.py` | 335 | Build a P1A B4 back-strand anchor/mask numeric probe for G3 review. |
| `build_cubism_v2_g4_b4_b5_focused_followup_packet_002.py` | 298 | Build the v22 G4 B4/B5 focused follow-up packet. |
| `build_cubism_v2_g4_codex_provisional_visual_decisions_002.py` | 167 | Seed v22 G4 visual decisions from current success-pattern evidence. |
| `build_cubism_v2_g4_compact_visual_review_surface_002.py` | 230 | Build a compact G4 visual review surface for character 002 v22. |
| `build_cubism_v2_g4_g5_material_promotion_readiness_002.py` | 241 | Build G4/G5 material promotion readiness after combined G3 context review. |
| `build_cubism_v2_g4_p0_b5_followup_decision_packet_002.py` | 277 | Build the v22 G4 P0 B5 follow-up decision packet. |
| `build_cubism_v2_g4_p0_torso_shoulder_decision_packet_002.py` | 264 | Decide the three P0 torso/shoulder rows after G4 torso selection. |
| `build_cubism_v2_g4_torso_base_regen_candidate_002.py` | 320 | Build the v22 G4 generated torso_base candidate packet. |
| `build_cubism_v2_g4_torso_base_regen_overlay_qa_002.py` | 325 | Focused overlay QA/triage for the generated v22 G4 torso_base candidate. |
| `build_cubism_v2_g4_torso_base_regen_review_packet_002.py` | 309 | Build the v22 G4 torso_base regeneration/review packet. |
| `build_cubism_v2_g4_torso_selected_manifest_overlay_qa_002.py` | 201 | Build overlay QA for the G4 torso-selected 64-part manifest variant. |
| `build_cubism_v2_g4_torso_selected_review_reduction_packet_002.py` | 311 | Build compact G4 review/reduction packet after generated torso selection. |
| `build_cubism_v2_g4_visual_decision_packet_002.py` | 308 | Build the v22 G4 visual decision packet for character 002. |
| `build_cubism_v2_g4_visual_decision_route_plan_002.py` | 272 | Build a route plan from v22 G4 visual decisions. |
| `build_cubism_v2_g5_hairfront_motion_readiness_acceptance_002.py` | 214 | Build the v22 HairFront motion-readiness acceptance packet. |
| `build_cubism_v2_g5_hairfront_motion_readiness_preview_002.py` | 286 | Build a pre-G7 HairFront motion-readiness preview packet. |
| `build_cubism_v2_g5_hairfront_preview_codex_triage_002.py` | 249 | Build Codex triage for the v22 HairFront pre-G7 motion preview. |
| `build_cubism_v2_g5_material_acceptance_from_prep_002.py` | 324 | Build the v22 G5 material acceptance packet from the latest prep packet. |
| `build_cubism_v2_g5_material_acceptance_reduction_route_002.py` | 248 | Reduce the v22 G5 material acceptance surface into route phases. |
| `build_cubism_v2_g5_prep_from_torso_selected_002.py` | 293 | Build the current G5 prep packet from the torso-selected v22 manifest. |
| `build_cubism_v2_g5_primary6_codex_decisions_002.py` | 213 | Record Codex provisional decisions for the v22 G5 primary-six rows. |
| `build_cubism_v2_g5_secondary_hairfront_reduction_002.py` | 213 | Reduce the remaining v22 G5 context/HairFront rows after primary6. |
| `build_cubism_v2_g6_hairfront_anchor_correction_input_002.py` | 240 | Build G6 HairFront anchor-correction input and override template. |
| `build_cubism_v2_g6_hairfront_anchor_probe_002.py` | 357 | Build a G6 HairFront anchor/motion-envelope probe packet. |
| `build_cubism_v2_gate_evaluation.py` | 300 | Evaluate whether the Cubism v2 review gate itself is calibrated. |
| `build_cubism_v2_group_position_clean_candidate.py` | 288 | Combine 8065 position success with 8066 clean-neutral opacity safely. |
| `build_cubism_v2_imagen_keypose_input_pack.py` | 367 | Build an Imagen input pack for clean sockets and eye/mouth keyposes. |
| `build_cubism_v2_layer_alone_qa.py` | 10 | Compatibility wrapper for the G1.5 layer-alone QA gate. |
| `build_cubism_v2_localization_validation_report.py` | 153 | Summarize the manual semantic override localization split validation. |
| `build_cubism_v2_manual_aligned_candidate_002.py` | 162 | Apply saved manual eye/mouth anchor alignment to character-002 keypose layers. |
| `build_cubism_v2_material_asset_manifest.py` | 287 | Build the material asset manifest for candidate_002. |
| `build_cubism_v2_material_contact_sheet.py` | 133 | Build a one-page-ish contact sheet for generated Cubism v2 material assets. |
| `build_cubism_v2_material_fix_batch_report.py` | 143 | Summarize material fix batch 001 for candidate_002. |
| `build_cubism_v2_material_pack_first_overlay_qa_002.py` | 227 | Build overlay QA sheets for character-002 material-pack-first candidates. |
| `build_cubism_v2_model_edit_assembly_qa_002.py` | 146 | Build clean-base assembly QA sheets for character-002 model-edit candidate. |
| `build_cubism_v2_model_edit_clean_base_candidate_002.py` | 230 | Build a character-002 clean-base candidate from a model-edit source. |
| `build_cubism_v2_model_edit_hybrid_candidate_002.py` | 108 | Build model-edit v3 hybrid candidate. |
| `build_cubism_v2_model_edit_mouth_alpha_candidate_002.py` | 134 | Build model-edit v4 by removing skin alpha from mouth expressions only. |
| `build_cubism_v2_model_edit_strict_mouth_candidate_002.py` | 106 | Build model-edit v4 strict-mouth candidate. |
| `build_cubism_v2_new_model_part_spec.py` | 311 | Build the project-specific Cubism v2_standard new model part spec. |
| `build_cubism_v2_no_wide_open_candidate_002.py` | 91 | Build character-002 candidate that excludes the bad wide-open mouth visually. |
| `build_cubism_v2_p0_torso_v2_manifest_overlay_qa_002.py` | 195 | Build overlay QA for the P0 torso v2 64-part manifest variant. |
| `build_cubism_v2_part_localization_template.py` | 190 | Convert manual semantic overrides into a reusable part localization template. |
| `build_cubism_v2_pre_generation_readiness_spec.py` | 363 | Build the Cubism v2 new-character pre-generation readiness spec. |
| `build_cubism_v2_review_manifest.py` ⚠️ | 534 | Build the Cubism v2 Korean review manifest. |
| `build_cubism_v2_review_packet.py` | 232 | Build compact human review packets for the Cubism v2 review app. |
| `build_cubism_v2_roi_guided_semantic_remask.py` | 407 | Build ROI-guided semantic remask layers from manual localization seeds. |
| `build_cubism_v2_semantic_owner_map.py` | 10 | Compatibility wrapper for the G1.5 semantic owner-map gate. |
| `build_cubism_v2_semantic_purity_gate.py` ⚠️ | 739 | Build and apply the Cubism v2 G1.5 semantic purity gate. |
| `build_cubism_v2_smile_open_mouth_packet_002.py` | 457 | Build a smile-open-only mouth keypose packet for Character 002. |
| `build_cubism_v2_source_inpaint_clean_bases_002.py` | 225 | Build source-face inpaint clean-base candidates for character-002. |
| `build_cubism_v2_validator_fixtures.py` | 326 | Build validator fixtures that test the Cubism v2 review gate itself. |
| `cubism_v2_material_asset_lib.py` | 426 | Helpers for the Cubism v2 material asset draft pipeline. |
| `generate_cubism_v2_full_canvas_material_assets.py` | 98 | Generate full-canvas Cubism v2 material assets from the manifest. |
| `generate_cubism_v2_keypose_pngs_from_pack_local.py` | 309 | Generate local clean-socket/keypose PNG candidates from the prepared input pack. |
| `normalize_cubism_v2_material_pack_first_002.py` | 204 | Normalize character-002 material-pack-first raw outputs into 2048 RGBA layers. |
| `process_generated_eye_sheet_v19_002.py` | 188 | Normalize generated Character 002 eye sheet into v19 full-canvas eye assets. |
| `process_generated_smile_mouth_sheet_002.py` | 246 | Process generated chroma-key smile mouth sheet into Character 002 full-canvas mouth layers. |
| `rebuild_cubism_v2_face_detail_masks.py` ⚠️ | 726 | Rebuild Cubism v2 face detail masks from saved manual localization ROIs. |
| `repair_cubism_v2_neutral_composite.py` | 453 | Repair the Cubism v2 material pack neutral composite toward the canonical PNG. |
| `repair_cubism_v2_semantic_masks.py` | 10 | Compatibility wrapper for targeted Cubism v2 semantic remasking. |
| `run_cubism_v2_imagen_keypose_generation.py` | 272 | Generate clean-socket/keypose PNGs with Vertex Imagen edit API. |
| `seed_cubism_v2_material_review_first_pass.py` | 133 | Seed a conservative Codex first-pass review for Cubism v2 material assets. |
| `setup_mps_compat_002.py` | 192 | Prepare the Apple Silicon MPS compatibility experiment. |

## material-psd — 소재 팩·PSD 빌더 (5)

| 파일 | LOC | 설명 |
|---|---:|---|
| `build_concept_psd_candidate.py` | 250 | Build a gated PSD candidate for concept-regeneration-001. |
| `build_cubism_material_pack.py` | 8 | CLI wrapper for building the Cubism material pack. |
| `cubism_material_pack.py` ⚠️ | 789 | Build and validate Cubism-import material packs for Vtube. |
| `export_rigger_handoff.py` | 8 | CLI wrapper for exporting the Cubism rigger handoff. |
| `prepare_concept_psd_smoke_parts.py` | 192 | Prepare clean technical-smoke parts for concept PSD import testing. |

## legacy-misc — 기타·레거시 (25)

| 파일 | LOC | 설명 |
|---|---:|---|
| `apply_mps_manual_mask.py` | 193 | Apply a human-painted review mask to a Mac MPS See-through candidate. |
| `blink_apply_review_001.py` | 295 | Apply saved blink review placement to staged blink layers. |
| `blink_stage_001.py` ⚠️ | 662 | Create and validate staged blink full-canvas layers. |
| `blink_stage_review_server.py` | 70 | Serve Blink Stage 001 preview and save label/review evidence. |
| `bootstrap_mini_cubism_pack_splitter_v0.py` | 310 | Bootstrap Mini Cubism pack-splitter-v0 experiment inputs. |
| `build_concept_bootstrap_parts.py` | 183 | Create rough full-canvas concept part candidates for visual review. |
| `build_cubism_mvp_rig_smoke_pack.py` | 362 | Build Cubism FREE-limit audit and MVP rig smoke checklist. |
| `build_mps_candidate_review_sheet.py` | 234 | Build a visual contact sheet and triage report for MPS See-through candidates. |
| `build_mps_cleanup_candidates.py` | 244 | Build cleanup candidates for failed MPS See-through semantic layers. |
| `build_pack_model_candidate_comparison.py` | 382 | Build a model-candidate comparison report for Mini Cubism pack splitter. |
| `build_review_manifest.py` ⚠️ | 702 | Build the unified part-purity review manifest. |
| `build_roi_cleanup_candidates.py` | 386 | Build ROI-focused cleanup candidates for MPS See-through parts. |
| `force_imagen_front_hair_arms_pass.py` | 254 | Force-promote Imagen front hair and both arms for MVP PSD progression. |
| `map_mini_cubism_dedicated_layers.py` | 161 | Gate See-through layers against the Mini Cubism dedicated v1 taxonomy. |
| `mini_cubism_preview_server.py` | 229 | Serve the Mini Cubism v0 preview app and project files. |
| `mouth_apply_delta_001.py` | 392 | Apply saved mouth manual delta to new generated mouth sheets. |
| `production_canvas_2048_smoke.py` ⚠️ | 983 | 2048 production canvas smoke tests for Vtube layer candidates. |
| `review_app_server.py` | 431 | Local server for the unified part-purity review UI. |
| `review_server_2048.py` | 61 | Local review server that saves manual Vtube adjustment evidence. |
| `run_live2d_core_api_extractor.py` | 320 | Extract Core-backed runtime structure from the Live2D strong model sandbox. |
| `run_mps_compat_matrix.py` | 226 | Run the See-through Apple Silicon MPS compatibility matrix. |
| `seed_imagen_live2d_technical_review.py` | 177 | Seed safe technical review verdicts for Imagen Live2D candidates. |
| `setup_imagen_live2d_experiment.py` | 222 | Prepare an Imagen-generated Live2D front-canonical experiment. |
| `split_mini_cubism_app.py` | 149 | AUTORIG-RUNTIME-SPLIT-001: mini_cubism_app/src/app.js(1,673줄 모놀리스)를 ES 모듈로 분할한다. |
| `tune_mini_cubism_keyforms.py` | 211 | Generate and rank conservative Mini Cubism keyform tuning candidates. |

