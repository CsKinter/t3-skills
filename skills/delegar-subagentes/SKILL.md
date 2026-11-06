---
name: delegar-subagentes
description: Use before launching, monitoring, verifying or merging delegated children (T3 delegate_task to OpenCode Go / Claude models), and when picking a model for a child. Covers routing with an evidence-based scorecard, brief template, monitoring without polling, verification before merge, and the living lessons list. Built on the ViQSilent RMS work; update it after every child finishes.
---

# Delegating to subagents (living protocol)

This skill is **living**: after each child finishes, update the scorecard and the lessons with dated evidence (what model,
what task, outcome, time). Rules change when evidence changes; don't keep a rule the data contradicts.

The user's own preferences outrank everything here. Current ones (2026-11-05):
- Full GLM-5.3 is out (burned credits). Hard cases escalate to **Sonnet** (Claude subscription), not to pricier OpenCode models.
- Haiku 5.5 runs from the **Claude subscription** (provider `claudeAgent`, model `claude-haiku-5-5`), not OpenCode
  (OpenCode has a monthly cap; Claude only 5 h / weekly windows, shared with Opus).
- Qwen3.8 Flash is on careful trial: measure usage (user snapshots the OpenCode console before and after).

## 1. Routing

| Task type | Default | Fallback |
|---|---|---|
| Numerical diagnosis, PF/DSL semantics, solver bugs, load flow | `opencode-go/deepseek-v4.1-flash` variant `max` | `opencode-go/glm-5.3-flash` `high` only if DeepSeek is capped |
| Cheap diagnosis (find the missing rule, no code) | `opencode-go/qwen3.8-flash` `xhigh` (deepest diagnosis in A/B, $0.26/task) | Haiku 5.5 via `claudeAgent` (cleaner protocol, uses the Claude sub) |
| Mechanical edits, search, boilerplate | DeepSeek V4.1 Flash `high` or GLM-5.3 Flash `high` | MiMo-V2.6-Flash |
| Prose summaries (manuals) | MiMo-V2.6-Flash | — |
| Hard / repeatedly BLOCKED | Sonnet via `claudeAgent` (sparingly) | — |

Never: kimi-k3.1-pro or gemini-4-argon in tool loops. Option name for OpenCode is `variant` (values per model: check
`orchestrator_capabilities` with `search`). Quota per 5 h on Go Plus: DeepSeek V4.1 Flash ~86.7k requests, GLM-5.3 Flash
~19k, Qwen3.8 Flash ~16k, Haiku 5.5 ~15k (OpenCode copy; we use the Claude one). DeepSeek peak pricing 01–04 and 06–10 UTC
Mon–Fri.

Observed cost per request on Go Plus (console, 2026-11-06 after 6 Qwen tasks): DeepSeek V4.1 Flash ≈ $0.0024 (8,074 req,
$19.31), Qwen3.8 Flash ≈ $0.0033 (832 req, $2.78), GLM-5.3 Flash ≈ $0.0056, full GLM-5.3 ≈ $0.039. Per TASK Qwen is
cheaper: ~150 requests ≈ $0.45–0.50 per task (5 tasks after the A/B: 731 req, $2.52). DeepSeek per task is roughly
$1–1.4 at most (its month total also covers work before the scorecard), because it runs longer loops (it also fixes more). Qwen implementation trial (11-06): protocol fixed by the `date` rule, code real and tested, but it over-engineered a fix
that doesn't reach PF. 2nd trial (SVC usetp, 11-06): merged — refuted its own prior diagnosis, fix by the TechRef, ~50 min, clean log.
Use Qwen for diagnosis and small, well-specified implementations (now 6 useful / 7 trials — the 5th a well-argued no-fix finding; the DdA meter fix was a real open-ended diagnosis too); DeepSeek for open-ended fixes.

## 2. Scorecard (evidence, newest first)

| Date | Model | Task | Result | Time | Protocol |
|---|---|---|---|---|---|
| 11-06 | DeepSeek V4.1 Flash max | Profile + speed up the RMS step (~55 s per 2 ms) without changing numbers | DONE: profiled first — 69 % of the step was `Jf[:nx,:] = I − h/2·Jf` on a LIL matrix, not the FD Jacobian everyone assumed; COO assembly, fixed per-device template, cached network block; caught a 7e-8 trajectory drift from SuperLU pattern (explicit zeros) and fixed it to bit-identical; found the saved pickles were silently truncated and regenerated them. Step 7.1–7.4×, init 197→149 s; my check: max|dif| 0.0 over 25,292×6; 10 tests; merged f8dec91 | ~1 h of 2.5 | Clean; declined coloring/AD because they'd change numbers (as briefed) |
| 11-06 | DeepSeek V4.1 Flash high | Measurement-only long run to 1 s vs PF snapshots 0.01/0.1/0.5/1.0 (no engine change) | PARTIAL, high value: reached 0.1 s (p90 2.5e-4, non-inherited max 2.34), engine cannot pass 0.102 s (TAIRA Clock boolean loop in Newton) and fails at 0.012 s in a single call; ran a clean A/B (no comparisons → identical) to rule out its own instrumentation; caught its own t0-freeze script bug; 9 prioritized drift candidates with PF's 0.5/1 s projections (SAN ISIDRO xtv2 opposite sign, EL MAITEN pitch ramp PF=0, PSS2B not decaying, CHAPIQUIÑA AVR 12× sensitive) | ~3 h of 4.5 | Clean; real timestamps; honest PARTIAL |
| 11-06 | DeepSeek V4.1 Flash max | PSS2B/AVR group drifts in 10 ms (CTA x8 −0.054 vs −0.032, CTM3TG, RCOL-U2 AVR, Pehuenche UEL) | DONE as a finding, no engine change: UTERM is the first input to move (flow 1.002697 → PF 1.003140 / VS 1.003046 at t0+); Td=0.02 s + 8 LeadLags amplify it; decomposed ANDINA by input (U −1.57e-5, Q +7.8e-6, P +1.9e-6); proved fidelity by feeding PF's t0 inputs into our model (reproduces PF's −1.712e-5); PANGUE (no UTERM) as control 3 % vs 67–77 %. Points the gap at flow→dynamic t0 voltage. 1 pinning test; merged a790f07 | ~1.5 h | Clean; used the control case I suggested in the brief |
| 11-06 | Qwen3.8 Flash xhigh | GUACOLDA U3 drp ur/ui 0.877 vs PF 0.956 (ratio = 13.3/14.5 kV) | DONE: found the producer is the StaVmea (i_mode=1) scaled to the RMS bus's max uknom instead of the connected terminal's; same rule as the flow fix be7e629; showed the machine itself was already right and vco/pss were just propagation; also fixed `int(0 or 1)` collapsing i_mode=0 (inert in 2608: 0 meters use it, matters for 25F); 8 inherited vars resolved, t0 0 worse, 10 ms p90 7.81→7.75e-5; merged bae4567 cleanly on top of LA CRUZ (both in sen.py) | ~1 h | Clean; checked other ugn≠kv machines (VOLCAN, PILMAIQUEN) on its own |
| 11-06 | DeepSeek V4.1 Flash max | REPC_A LA CRUZ SOLAR Pbranch/Qbranch (0.096/0.036 vs PF 0.110/0.002) | DONE: PF meters the J3-1 coupler at 220 kV; the KCL section sum omitted the load C. SQM La Cruz 23 (warned 'not attributable' and skipped) → added section loads with the same exponential model as `Carga` (shared helper); now 0.110122/0.002044 vs PF 0.110122/0.002043; only cubicle meter in the SEN with loads, so nothing else moved; 3 tests; t0 0 worse; 10 ms p90 7.81→7.75e-5; merged a2e044a | ~1 h | Clean; read the old warnings in the code as clues |
| 11-06 | Qwen3.8 Flash xhigh | LA CABAÑA/CUEL Current Controller xd/xq (null direction; my brief: check frame consumers of Pmr/Pmi) | DONE: confirmed the hypothesis — Pmr/Pmi feed the ElmGenstat `u1r_in/u1i_in` slot (22 plants wire it; it was being dropped as 'unsupported'); PF's init rule e = u + z·i with default uk 10 %/Pcu 10 kW reproduces Pmr/Pmi to 2e-16 (CUEL 1e-5); xd/xq 4.6→<1e-4; flexible-exigency rule so WECC sources keep their own logic; refuted the earlier 'stored u0' child; 10 ms p90 7.84→7.81e-5. Merge conflict with the parallel xspeed child (same class) resolved by me; I made bad uk/Pcu non-fatal | ~1.5 h | Clean |
| 11-06 | DeepSeek V4.1 Flash max | ElmGenstat `xspeed` constant 1.0 → measured terminal frequency (25F-relevant) | DONE: found the rule in TechRef (output "Frequency" of all 4 RMS models), rejected PLL/system-frame readings with data (constant-Z/P models publish xspeed and have no PLL; 47/111 Genstat lack a PLL); reused PF's StaVmea `fe` filter (Tfe=3/Fnom) as 2 states, pure residual; synthetic ramp test; 10 ms identical (no event), t0 0 worse; merged d32aa5f. Honest gap: PF snapshots don't record fpv over time, so the filter is unverified until an event case | ~45 min | Clean |
| 11-06 | DeepSeek V4.1 Flash max | Load flow: Q limits from IntQlim capability curves (P and U dependent, inputmod 0/1, ngnum) + outer loop for unknown U + extractor for future DBs | DONE: verified the pu/ngnum scaling against PF's t0 itself; 2608 unchanged as predicted (94/94 inside, ΔQ 0, slack equal); 15 synthetic tests; t0 0 worse; merged 7135948 | ~1 h | Clean; curves load only via `VIQSILENT_QLIM` for 2608 (stored project lacks them) |
| 11-06 | DeepSeek V4.1 Flash high (Windows) | Mechanical PF-bridge run: IntQlim extraction script (mine, SHA-checked) | DONE on retry: 1st run correctly STOPPED at step 1 (client project active, bridge down) without touching anything; after the user switched to 2608, 94 curves, 0 errors, 6.5 s, zip verified | minutes | Clean; exact runbook followed |
| 11-06 | Qwen3.8 Flash xhigh | SAN JUAN park controller `prefcurt2` 0.3358 vs PF 0.3392 (+ 1.268 kick at 10 ms) | DONE as a finding, no engine change: translation correct (selfix gives both fields the common setpoint); PF's t0 is out of equilibrium (`perr` = −0.012 MW from Pref/p mismatch, ×Kp_p 1.5 = exactly the t0 diff); the PF-rule anchor would worsen 0.0034→0.0186, so it rightly declined. 4 tests pinning the semantics merged (0b4143f); t0 0 worse, 10 ms identical | ~1.5 h | Clean; correctly refused a fix that matches PF's rule but not PF's numbers |
| 11-06 | DeepSeek V4.1 Flash max | Newton fails t=2 ms after PPC merge (ATACAMA PQ meter, 3.5e-4) | DONE: cause was not the |i| kink but the FD Jacobian of the module row taking a chord on a stiff coupler (y≈6e3, |i|≈1.6e-3) → wrong Newton sign; general fix: chain-rule rows for modules (`filas_abs`), equations untouched; + side bug (MedidorCupon assumed 2 buses); 10 ms 6/6, p90 0.00124→0.00114, also verified on a3dead1; I re-ran 10 ms myself → merged (integration c177fd4) | ~1.5 h | Clean; rejected the brief's hypothesis with evidence |
| 11-06 | DeepSeek V4.1 Flash max | PPC ANDES III anchoring (impl. from Qwen+Haiku diagnoses) | DONE: real root cause was case-sensitive frame signal names (id_ref/Id_ref), + flow anchors; PPC 0.0118, WD3 0.0019; t0 63 better/0 worse merged; **10 ms fails at 2 ms (3.5e-4, ATACAMA PQ meter)** → parked on t3/integ-ppc, follow-up child | ~3 h | Clean; brief lacked 10 ms acceptance (my gap) |
| 11-06 | Qwen3.8 Flash xhigh | Implementation trial: LA CABAÑA Current Controller init | PARTIAL: proved init subdetermined (null space dim 2), general SVD-anchor rule + 9 tests, deterministic; but anchors to 0 vs PF 1.0166 and adds 135 lines to compilar.py → held, not merged. Side finding: SVC delta = `usetp` unwired in assembly | 1 h 19 min | **Real timestamps this time** (`date` rule worked); one 47-min log gap; notes in E only |
| 11-06 | DeepSeek V4.1 Flash max | PE CALAMA pitch init (Theta 0 vs PF 6.69°) + FINIS TERRAE x_mq | DONE both: (1) loopinc solve fell into a local minimum of a non-monotone WTGAR_A2 parabola → sweep [xmin,xmax] like PF and retry from the 4 best starts; (2) rejected the prior child's "flow difference" hypothesis: the parent frame of an ElmDsl shared between frames was never assembled (PPC slave B3 had p/q/u/fe unwired). t0 18 better/0 worse; 10 ms max 1.34→1.10; merged d02b71c, my 10 ms 6/6 p90 0.00073 | ~2 h | Clean; did the secondary task too |
| 11-06 | DeepSeek V4.1 Flash max | REEC_B Pref 1.001 vs PF Pe (GABRIELA, VICTOR JARA) + PPC fpv = voltage | DONE (retry after `[overloaded]` mid-run): converter REGC_A is a compiled BlkDef → id_ref unwired → inc(Pref) loop fell to Pmax+0.001; anchor control Ipcmd/Iqcmd to flow current when converter slot fails. Rejected brief's f→fe alias hypothesis: fpv wired from ElmGenstat `xspeed` that didn't exist. Also closed QUILLAGUA II, NUEVA QUILLAGUA, SAN ANDRES; correctly reported G1 does NOT share the cause. t0 29 better/0 worse; merged 987197a, my 10 ms 6/6 p90 0.00070 | ~1.5 h | Clean; flag: xspeed constant 1.0 (no frequency tracking) |
| 11-06 | DeepSeek V4.1 Flash max | Load flow: PANGUE U1/U2 stuck at −13.2 Mvar (PF −19/−24.7) | DONE: units with a capability curve (`pQlimType`) — PF hides cQ_min/cQ_max (TechRef); found the rule in the manual, ruled out ElmStactrl/ngnum. 10 ms p90 0.00070→0.00010 (7×), ElmSym max 0.46→0.04; t0 637 better/108 worse (small Q shifts + null-space CABAÑA), honestly reported; merged d27230c, my run reproduced exactly | ~1.5 h | Clean; flagged pending IntQlim extraction |
| 11-06 | Qwen3.8 Flash xhigh | VSC DIEGO DE ALMAGRO Qac (−0.614 vs PF −1.020) meter | DONE: rejected brief's 'base' hypothesis — incomplete KCL cut of the cubicle section (Tr3 legs, coupled-line ElmTow sections, node admittances); B991 KCL closes exactly; gated off busbar meshes after spotting it degraded SAN ANDRES; 3 commits, honest limitations list. t0 36 better/0 worse; merged 9d26d0a on top of PANGUE, my 10 ms p90 0.000083 | ~1.5 h | Clean; shunt filter by naming convention (fragile) |
| 11-06 | DeepSeek V4.1 Flash max | HP LAJA I governor moves at t0+ (pt −4 % vs PF +0.5 %) | DONE: BlkRef signal entering the macro's only input via port 1 was dropped by the flattener → Kaplan gate init 0.734 above HS_mx 0.72 → governor active; general port remap (only when counts match, with warning). LAJA pt to 1.9e-7; ElmSym max 0.041→0.016; t0 0 worse; correctly diagnosed secondary (SAN ISIDRO) as flow-voltage-driven, out of scope. Merged 0338caa, my 10 ms p90 0.000078 | ~1.5 h | Clean |
| 11-06 | Qwen3.8 Flash xhigh | SVC `nncap` (TechRef eq. 23) + PAN DE AZÚCAR flipflop root | DONE: confirmed my hypothesis (nncap wired by name + initialised from the flow → PdA takes the flow's root 0 = PF); 6 tests; t0 4 better / 1 worse (MAITENCILLO nncap: PF's stored u0 doesn't reproduce its own flow, documented); **10 ms p90 0.00102→0.00076, non-inherited max 0.98→0.15** (San Isidro xtv2 and PSS x8 now move like PF); ff-merged 7c4acdd | ~1 h | Clean, real timestamps, flagged the one regression honestly |
| 11-06 | Qwen3.8 Flash xhigh | SVC `usetp` wiring (2nd implementation trial) | PARTIAL by its own strict reading, effectively DONE: refuted its own earlier diagnosis with PF data (usetp comes from the BlkDef `inc()`); real cause = `gatea`→ElmSvs link dropped in assembly; fix per TechRef eqs. 22/24 + 6 tests; 4 SVCs to PF (gatea dif 4.5–69° → 0.03–0.31°); 10 ms p90 0.00105→0.00102; one documented regression (PdA nncap flipflop 0→1), accepted; merged bc0749f. Missed TechRef eq. 23 (`nncap`) → follow-up | ~50 min of 1 h 30 | **Real timestamps, clean log, honest status** |
| 11-06 | DeepSeek V4.1 Flash max | REPC plant controllers t0 (AZABACHE xp 8.50 vs 0.118; SAN ANDRES 1.53 vs 0.027) | DONE (retry after a `prefill_cap_refused` start failure): meters with i_mode=1 used 1 MVA base instead of the measured element's rating (Tr2/Tr3/line); PQ meter on a coupler inside a busbar mesh now measures the terminal net. Both now match PF to ~1e-4; t0 16 better/0 worse; 10 ms p90 0.00107→0.00105; ff-merged (04b5ad5). Flag: StaImea keeps section sum in the mesh case, fitted to PF data | ~1.5 h | Clean; named out-of-scope leftovers (FINIS TERRAE, MAITENCILLO) |
| 11-06 | DeepSeek V4.1 Flash max | Meter fix breaks Newton at 2 ms (residual 1.0) | DONE: meter fix correct; it moved MALLECO NORTE WP `xi` to PF's value, which exposed PSS2B CTM3TG `x24` 1→0 flipping a gain-1e6 `lim` in one step (no α descends); fix: ≤5 bounded full non-monotone steps per step, fresh Jacobian only, final residual still decides; + test; merged onto c177fd4 (test conflict, kept both), my 10 ms 6/6, p90 0.00114→0.00107 | ~2 h | Clean; solver relaxation, so watch it on longer runs |
| 11-06 | DeepSeek V4.1 Flash max | RMS meter sign on ElmCoup cubicle (STATCOM Qmeas) | PARTIAL by its own threshold but correct: PF rule (i_orient, section incl. zero-impedance bridges), +4 tests, 58 better/0 worse in t0, residual 3.4 % traced to flow V at 46 kV; merged, then **reverted: breaks Newton at t=0.002** (brief only asked for t0) | ~1.5 h | Clean; honest PARTIAL with the cause measured |
| 11-06 | DeepSeek V4.1 Flash max | STATCOM ENTRERIOS droop (ElmCoup cubicle) | DONE, 2 root causes (droop measured in an ElmCoup cubicle; OLF minRealisticVoltage rejecting PF's branch), general fix + 3 tests; merged; combined flow dU p90 0.0149→0.0014, max 0.84→0.028 | ~2 h | Clean; ran from 663e2e6 without be7e629 but merged cleanly |
| 11-06 | DeepSeek V4.1 Flash max | WD3 init SVD after be7e629 (flow fix) | DONE, root cause (unseeded h2≈1.28e12 >1e9 cap), general fix + tests, t0 g 3.16→1.0, 10 ms run itself; merged | ~1 h | Clean log every ~10 min; attributed 118 regressions to the flow change, partly wrong (see lessons) |
| 11-05 | Qwen3.8 Flash xhigh | A/B: PPCControl ANDES III t0 | PARTIAL, deepest diagnosis (exact missing link in `_exigencias_tardias` + 2nd issue), no engine code | 36 min, 215 items | **Fake timestamps in log, claimed "2 h cap reached" at 36 min**; committed notes into repo `docs/`; usage **101 requests, $0.26** (≈$0.0026/req, same as DeepSeek) |
| 11-05 | Haiku 5.5 high | A/B: PPCControl ANDES III t0 | PARTIAL, sharp verified diagnosis, no code | 26 min (cap 2 h) | Clean log + schema; **gave up early** without testing its hypothesis |
| 11-05 | DeepSeek V4.1 Flash max | Saturation breaks Newton t=0 | DONE, exact root cause (impure F(z)), test, 10 ms verified | 48 min | Clean |
| 11-05 | DeepSeek V4.1 Flash max | Load flow VS vs PF | PARTIAL, strong diagnosis (STATCOM ENTRERIOS, be7e629 breaks WD3) | ~3 h | Log silent 70 min |
| 11-05 | GLM-5.3 Flash high | Synchronous saturation | Good physics (t0 30–100x better) but left impure residual that broke Newton | ~1.5 h | **Cut turn mid-sentence**, no exit schema |
| 11-05 | GLM-5.3 (full) | G4/G5/G6 init rules | Regression (f 6161→5.4e8), kept running after "completed", background processes | long | Poor; also burned credits → removed |
Reading so far: DeepSeek V4.1 Flash max is the most reliable for closing a task. In the A/B, both Haiku and Qwen stopped at
a diagnosis with most of the budget left; Qwen's was deeper and more actionable, Haiku's cleaner and cheaper. Neither
implemented. Useful pattern: cheap diagnosis by Haiku/Qwen → implementation by DeepSeek with both diagnoses as traspaso
(first run "PPC ANDES III: anclaje PF", 11-06: worked — DONE, though the root cause was a third thing neither diagnosis named). DeepSeek closed 16/16 engine tasks on 11-05/06 (one PARTIAL only by an over-tight threshold). GLM Flash is a fallback. Don't trust children's self-reported clock
times; use the thread's createdAt/completedAt.

## 3. Brief

Keep reusable rules in a shared file the child reads first (ViQSilent: `estudios/cen_2608/referencia/v5/completa/encargos/comun.md`)
and one file per task (`encargos/<tarea>.md`). The `task` text stays short: preparation (`git merge --ff-only <commit>`,
`git checkout -b <branch>` — new name if the branch exists), the two files to read, a 2-line summary, the exit reminder.

Every task file has: traspaso (exact paths, lines, numbers, what earlier children found and ruled out), what to do,
acceptance with numeric thresholds and the exact commands, its own data folder (`paso_vNN/`), branch name, time cap, and
what is out of scope (name the other children's areas so they don't collide).

Exit schema: STATUS / FILES_MODIFIED / COMMITS / VERIFICATION / KEY_FINDINGS (<300 words, no code or logs).

## 4. Launch and monitor

- `isolation: "worktree"` per child; worktrees start at the parent checkout, hence the ff-merge step.
- Record the start time (A/B: `E/ab_modelos.md`).
- Do not poll. Completion wakes the orchestrator. If the user asks how a child is doing: `tail` its `bitacora.md`; if
  silent, `t3_thread_read` view=activity, `afterPosition` = itemCount−12, `maxCharsPerItem` ≈300.
- Switching a child's model is cheap only before it has real work: cancel, then relaunch with a new branch name and the
  same data folder.
- Machine: 10 cores, 16 GB. Each heavy run (`medir_t0`, `validar_10ms`) uses ~1 core for 10–15 min of init; 4 children in
  parallel is fine. Don't `kill` by folder pattern (hit another child once).

## 5. Verify before merging (always, never trust the summary alone)

1. `git log <base>..<branch>`, `git diff --stat`, read the engine diff.
2. Clean tree, no leftover processes (`ps aux | grep -E "validar|medir"`).
3. Full suite: `/Users/vicentequinteros/ViQSilent/.venv/bin/python -m pytest -q --tb=short` (a subset once hid a failure).
4. Numbers: compare the child's JSON against the previous reference with a script (t0: `paso_v12/t0_b.json`;
   10 ms: latest `comparacion_pf_10ms.json`, now `paso_v48` at 0338caa (p90 0.000078); t0: `paso_v48/t0.json`). If the child skipped the 10 ms run, run it yourself in background with
   `WALL_LIMITE=3600`.
5. Merge `--no-ff` into the integration branch with the numbers in the message; rerun the full suite; log in the scorecard.

## 6. Lessons (dated; add new ones on top)
- 11-06 Performance briefs: demand a profile before any change and a bit-identity acceptance (trajectory max|dif|),
  and forbid trajectory-changing tricks. The hotspot was not where I guessed (LIL slicing, not FD). Also: when a brief
  hands children a saved artifact (pickle), load it once yourself first — mine was silently truncated.
- 11-06 Measure long before polishing short: 30+ merges tuned 10 ms while the engine could not integrate 0.1 s in one
  call. Run a long measurement child early in any new DB (25F) and keep one in the loop after big merges.
- 11-06 For 'model X drifts from PF' briefs, require the fidelity test: feed PF's own t0+ inputs into our model and
  compare. If it reproduces PF, the model is right and the gap is upstream (here: flow→dynamic terminal voltage), and
  the child can decline the fix with proof instead of tuning the model. Also give it a contrast case (PANGUE).
- 11-06 A t0 ratio that equals two nominal voltages (0.9172 = 13.3/14.5) is a base bug; put the ratio in the brief and
  Qwen closes it in ~1 h. Check any `int(x or default)` the child touches: it silently maps an explicit 0 to the default.
- 11-06 Existing `av.append("... no atribuible ...")`/"se omite" warnings in the engine are a map of known gaps: LA CRUZ
  REPC_A was exactly one of them (a load skipped in a meter's KCL section). When briefing a meter/assembly mismatch, tell
  the child to grep the run's warnings for the element first.
- 11-06 Parallel children that touch the same class (xspeed + CABAÑA both in `GenstatPF`) merge with conflicts and
  break each other's tests (new states → a test passing `x=[]`). Merge the second one by hand, run the full suite,
  and re-run 10 ms on the combined tree. When briefing parallel children, name the shared files.
- 11-06 Before sending a child to extract "stored" values through the PF bridge, look for a physical pattern in PF's
  numbers: LA CABAÑA's "u0 from case history" (prior child) had Pmr+jPmi at the terminal-voltage angle (1.5279 vs
  1.5280 rad), which points to a frame connection rather than history → a Mac-only diagnosis replaced a Windows run.
- 11-06 Three children in parallel (2 DeepSeek + 1 Qwen) on separate worktrees from the same base ran fine; a
  measurement-only child (no engine changes) is a good use of DeepSeek high for multi-hour runs.
- 11-06 PF's own t0 can be out of equilibrium (SAN JUAN: `perr` ≠ 0 from a Pref/p mismatch inside PF). A fix that
  follows PF's rule but moves the numbers away from PF's should be declined; a numbered no-fix finding plus tests
  that pin the semantics is a valid DONE. Say so in briefs so children don't force a fix.
- 11-06 PF-bridge extractions: I write the script (generic `GetAvailableAttributesAsJson` dump, no guessed
  attribute names), stage it with its SHA256, and a mechanical child runs it. Check the Mac's LAN IP first; it changes.

- 11-06 A child can fail at start with `prefill_cap_refused` (OpenCode Go capacity), leaving an empty worktree and branch at the base → check the branch has no new commits and no bitácora, remove the worktree, `git branch -D` the empty branches, and relaunch the same brief once.
- 11-06 Children that hit an unsupported (compiled/encrypted) BlkDef should anchor the init from flow data rather than invent the missing model, and must flag any constant they publish in its place (e.g. xspeed=1.0) — those are correct at t0 but silently wrong in events.
- 11-06 Same for `[overloaded]` mid-run (REEC_B child died ~26 min in, only setup + 2 probe scripts): check the bitácora, remove the empty worktree/branch, relaunch with a note pointing at the existing bitácora/probes and a fresh time cap. Infra failures don't count against the model's score.
- 11-06 `medir_t0` lists only models that still differ: a drop in model count (732→670) means models reached PF, not lost coverage. When a fix touches the load flow, expect hundreds of tiny moves both ways; judge worsenings by magnitude and by whether the variable feeds anything (null-space states with no consumer are cosmetic), and say so in the brief's acceptance.
- 11-06 Dynamic (non-inherited) errors are good child targets once t0 is mostly clean: LAJA's 10 ms drift came from a t0 error that was masked by compensation (pt matched, gate didn't). Brief them with 'which input moves first' probes.
- 11-06 Both 2 ms Newton failures had a cause other than my brief's hypothesis (FD chord on a stiff coupler; a gain-1e6 `lim` flip, not the meter) → phrase brief hypotheses as "suspect, verify or reject" and accept a rejected hypothesis as a good outcome. Two fixes from different bases merged cleanly in sequence when I re-ran 10 ms after each merge.
- 11-06 A clean t0 (58 better/0 worse) still broke the 10 ms run at t=0.002 → every brief that touches RMS devices or
  equations must require the 10 ms run in its acceptance, and I run it after every merge before calling it done. Bisect
  with a temporary worktree of the parent (`/private/tmp/...`: the script asserts the resolved path).
- 11-06 Child-written helper scripts may hardcode their output path (paso_v19/comparar_t0.py overwrote its own folder's
  JSON when reused) → check where a reused script writes before running it; prefer outputs next to the input.
- 11-06 Children's attribution of regressions ("comes from the flow change") can be wrong: LA CABAÑA xd flipped
  1.24→−3.63 with inputs unchanged to 1e-4, so the cause is an ill-conditioned init, not the flow. Before merging,
  check the inputs of the worst regressions in t0.json (`entradas_distintas` new vs base) and decide yourself.
- 11-06 `t0.json['modelos']` only lists models that differ from PF; model-count changes between runs are not lost models.
- 11-06 Qwen wrote invented times in its bitácora and stopped claiming the time cap had expired → measure time from the
  thread (createdAt/completedAt), and say in the brief "check `date` before writing a log line or claiming a cap".
- 11-06 Diagnosis-only outcomes are common for cheaper models → when a diagnosis exists, the next brief should be pure
  implementation with the diagnosis files as traspaso.

- 11-05 Children may end their turn mid-sentence with a long run pending → brief says "never end mid-sentence; wait or
  report PARTIAL". Check the actual worktree, not the summary.
- 11-05 Residual functions must be pure: device state mutated inside F(z) (saturation coefficients from the previous
  evaluation) silently breaks the finite-difference Jacobian and the line search. Tell children working on equations.
- 11-05 Load-flow changes can break downstream DSL init (WD3 `least_squares` "SVD did not converge" on non-finite values).
  A child chasing that for an hour on its own flow change was stuck → revert-and-note rule in comun.md.
- 11-05 Bitácora + anti-stuck rule (3 repeats or ~45 min without progress → BLOCKED) works; children still go silent for
  long stretches → require a line at least every 30 min.
- 11-05 Haiku reports PARTIAL with most of the budget left → for implementation tasks say "if you have a testable
  hypothesis and time left, test it in the engine before reporting".
- 11-05 A delegated `pytest` subset reported green while the full suite failed → always run the full suite myself.
- 11-05 Usage limits: commit the child's WIP before relaunching after a cap; ask the user (wait / other model) when OpenCode
  caps out.
