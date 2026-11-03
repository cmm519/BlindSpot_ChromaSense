# Increment 28: Team acceptance

### Main rules

- An agent cannot observe these rows. Do not simulate them, and do not mark a row as met without the team's reported result.
- Ask the user to run each check, and report the checklist. Keep the status `yellow` until the team reports every row.
- Do not change GitHub settings or spend provider money without the user's approval.

### Header

- **Increment:** 28
- **Capability:** Team acceptance
- **Status:** `Standard`
- **Depends on:** `27-measured-targets.md`
- **Traces to:** Rows in `srs.md` whose verification needs people, devices, a real provider, or repository settings
- **SRS IDs:** **SRS-NFR-004**, **SRS-NFR-005**, **SRS-NFR-012**, **SRS-NFR-014**, **SRS-NFR-017**, **SRS-NFR-018**, **SRS-NFR-021**, **SRS-NFR-022**, **SRS-NFR-025**, **SRS-NFR-026**, **SRS-NFR-031**, **SRS-NFR-033**, **SRS-NFR-034**, **SRS-NFR-038**, **SRS-NFR-039**, **SRS-NFR-040**, **SRS-NFR-042**

### Requirements

- **SRS-NFR-004** (should): AI interpretation, including comparison with the local analysis, shall return a result within 30 seconds under normal network conditions. (NFR-1.4; severe low-vision requirement; local-first change)
- **SRS-NFR-005** (must): The home page shall become interactive within 2 seconds on the LAN in the reference browser. (NFR-1.5)
- **SRS-NFR-012** (must): All interactive elements and dynamic results shall expose accessible names, roles, states, and updates to screen readers. (NFR-4.1; extended for low-vision access)
- **SRS-NFR-014** (must): The portal shall never use color, shape, pattern, or position as the only means of conveying information. (NFR-4.3; extended for low-vision access)
- **SRS-NFR-017** (must): A first time user with a profile set shall be able to enhance an image within 3 clicks of the home page. (NFR-4.5)
- **SRS-NFR-018** (should): The portal shall achieve a System Usability Scale score of 70 or higher in user testing. (NFR-4.6)
- **SRS-NFR-021** (should): At least 99 percent of sessions during beta testing shall complete without a server error. (NFR-5.3)
- **SRS-NFR-022** (should): The portal shall target 99 percent availability on the LAN host during the evaluation period. (NFR-5.4)
- **SRS-NFR-025** (should): AI legend mapping shall be at least 90 percent correct on the labeled chart test set. (NFR-6.3)
- **SRS-NFR-026** (should): Users shall achieve higher task accuracy with ChromaSense than with the original image or a global daltonization filter. (Section 8)
- **SRS-NFR-031** (must): Every pull request shall pass automated builds and tests before merging. (NFR-7.3)
- **SRS-NFR-033** (must): The portal shall listen on port 9090 on all host interfaces and be reachable at `http://<host-ip>:9090` from another device on the same LAN. (NFR-8.1)
- **SRS-NFR-034** (should): The project repository shall include a README and setup guide that explain how to start the portal and reach it from another device on the LAN. (Section 2.6)
- **SRS-NFR-038** (must): A user with no view of the screen shall be able to upload an image, set the profile, and get every color, shape, and text item with its flag. (NFR-4.1; inferred severe low-vision requirement)
- **SRS-NFR-039** (should): AI text and shape items shall each be at least 90 percent correct on a labeled test set of charts, maps, and flat graphics. (NFR-6.3; inferred severe low-vision requirement)
- **SRS-NFR-040** (should): At least 95 percent of text and shape items flagged verified shall be correct on the labeled test set. (NFR-6.3; inferred severe low-vision requirement)
- **SRS-NFR-042** (should): Local text and shape items shall each be at least 80 percent correct on the labeled test set of charts, maps, and flat graphics. (Local-first change)

### Capability

The team records the results that only people, real devices, a real provider, and repository settings can give.

### What may change

Only `prompts/tracking.md`, and defects that the team's results expose. Fix a defect in the owning part, and rerun that part's checks.

### What must stay

Requirements, thresholds, parts, and decisions stay as written.

### Implementation notes

Give the user this checklist, and record each answer in `prompts/tracking.md`:

| Needs | Rows | What the team does |
| --- | --- | --- |
| A chosen provider and key | SRS-NFR-004, SRS-NFR-025, SRS-NFR-039, SRS-NFR-040 | Choose the provider, adjust the two private wire format functions if needed, and run timed and labeled-set comparisons |
| A real labeled test set | SRS-NFR-025, SRS-NFR-039, SRS-NFR-040, SRS-NFR-042 | Supply charts, maps, and flat graphics with ground truth in `src/color_engine/tests/data/labeled/` |
| Second computer and phone | SRS-NFR-005, SRS-NFR-033, SRS-NFR-034 | Follow only the README from another device, and profile the home page in Chrome |
| Screen reader testers | SRS-NFR-012, SRS-NFR-014, SRS-NFR-038 | Do the walkthrough, the grayscale review, and the display-off task with NVDA on Windows and VoiceOver on a phone |
| User study | SRS-NFR-017, SRS-NFR-018, SRS-NFR-026 | Run the task-based study against both baselines |
| Beta period | SRS-NFR-021, SRS-NFR-022 | Read server logs and health checks. A health check requests `GET /`, because `srs.md` names no health endpoint |
| Repository admin | SRS-NFR-031 | Make the CI workflow a required check, and open a pull request with a failing test |

### Verification

Show each SRS observation in full:

- **SRS-NFR-004**: Timed Explain requests against the real provider on a normal connection each return with verification flags within 30 seconds.
- **SRS-NFR-005**: Chrome performance profiling from a second LAN device reports time to interactive under 2 seconds.
- **SRS-NFR-012**: axe reports no missing label violations on any page, and a screen reader walkthrough completes the enhance and interpret tasks and announces updated results.
- **SRS-NFR-014**: A grayscale and screen-reader review finds that each status, flag, pattern, and control state remains distinguishable and has a text equivalent.
- **SRS-NFR-017**: A Playwright run from the home page reaches the enhanced result in 3 clicks or fewer, and the user study confirms it.
- **SRS-NFR-018**: The mean SUS score from the task based user study is 70 or higher.
- **SRS-NFR-021**: Server logs from beta testing show at least 99 percent of sessions with no 5xx response.
- **SRS-NFR-022**: Periodic health checks during the evaluation period succeed at least 99 percent of the time.
- **SRS-NFR-025**: A comparison with the labeled ground truth reports at least 90 percent of legend entries correct.
- **SRS-NFR-026**: The study's task accuracy for ChromaSense is higher than for each of the two baselines.
- **SRS-NFR-031**: A pull request with a failing test shows a failed required check and cannot be merged.
- **SRS-NFR-033**: A second computer and a phone on the LAN each open that address and upload an image.
- **SRS-NFR-034**: A developer who follows only the guide starts the portal and reaches it from a second LAN device.
- **SRS-NFR-038**: With the display off, a tester using NVDA on Windows, and another using VoiceOver on a phone, completes the task and correctly reports the items in a test image and their flags.
- **SRS-NFR-039**: A comparison with the labeled ground truth reports at least 90 percent of text items and of shape items correct.
- **SRS-NFR-040**: A comparison of the verified items with the labeled ground truth reports at least 95 percent correct.
- **SRS-NFR-042**: A comparison with the labeled ground truth reports at least 80 percent of local text items and of local shape items correct.

Also confirm:

- The team reports a result for every row in the checklist.

Run from the repository root:

```
docker compose build
docker compose up portal
```

### Main rules again

- An agent cannot observe these rows. Do not simulate them, and do not mark a row as met without the team's reported result.
- Ask the user to run each check, and report the checklist. Keep the status `yellow` until the team reports every row.
- Do not change GitHub settings or spend provider money without the user's approval.
