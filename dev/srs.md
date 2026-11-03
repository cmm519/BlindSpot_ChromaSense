# Software requirements specification

You fill this file in stage 1 (see `README.md`).

State what the system must do only in this file. Class names and the directory tree go in `architecture.md` and `structure.md`. Do not name prompt files here.

Fill the **Required** sections before any agent runs. **Optional** sections may say `none`. The topics follow ISO/IEC/IEEE 29148:2018.

## Required: Identity

ChromaSense: AI Powered Color Accessibility Web Portal

## Required: Purpose

Who this specification is for, and what the build must satisfy.

This specification is for Team BlindSpot, the course instructor, testers, and the agents that generate and implement the build. The build must satisfy the requirements below, and every `must` verification must hold.

## Required: Scope

One paragraph: what the finished software does, who it is for, and the benefit.

ChromaSense is a server-side web portal, reached from a browser on the local network, that helps people with color vision deficiency (CVD) and low vision understand color coded information in images. Unlike a global color filter, it detects which colors are confusable for a specific user's CVD profile, enhances only those colors, and uses AI to explain the meaning of color coded content such as charts, maps, and legends. It presents analysis results in accessible text and can speak AI responses so users do not have to rely on seeing colors, shapes, or text. For users who can hardly see, it identifies the colors, shapes, and text in an image and reports whether each item was verified. It also includes a CVD simulator for people with typical color vision who want to review their content. Uploading an image starts the processing pipeline. Charts, maps, and flat graphics are the supported target for this release, and photographs are handled on a best effort basis.

## Required: Product perspective

Its relation to users and to any larger system. Name the external systems. If it stands alone, say so.

ChromaSense is a new, self contained product and is not part of a larger system. Users reach it with a web browser on a computer or phone on the same LAN as the server host. It has one external system: a third party vision language model (VLM) API, which only the server calls and which is needed only for AI interpretation.

## Required: Users

One line for each kind of user. Include what they already know how to do.

- Users with CVD (varying CVD type and severity, general web browsing skills) — make color coded images readable through enhancement, overlays, color identification, and the AI interpreter
- Students and professionals with CVD (frequently read charts, maps, and dashboards) — understand charts and maps through the AI interpreter, follow up questions, and overlays
- People with low vision (general web browsing skills; may use magnification, a screen reader, or speech output) — access color, pattern, and AI interpretation results without relying on visual-only cues
- People with severe low vision (can hardly see the screen, may have no CVD, use a screen reader or keyboard to browse the web) — have any color, shape, or text in an image identified and verified, and hear the results through a screen reader or spoken AI responses
- Designers, educators, and developers (typical color vision, produce visual content) — test how their content appears to CVD users with the simulator and confusion detection
- General public (general web browsing skills, curious about CVD) — see how images appear under each CVD type with the simulator

## Required: Product functions

A short overview. The testable statements go in the requirements table.

- Upload images from a file picker, by drag and drop, or from the clipboard, which starts the pipeline
- Select a CVD profile with type and severity, or state that the user has no CVD
- Simulate how an image appears to each CVD type
- Detect confusable color pairs for the active profile
- Enhance only confusable colors
- Add pattern overlays to confusable colors
- Identify the name and values of a color at a point chosen by click, tap, or keyboard
- Browse detected colors and confusable pairs through accessible text, including their color values and pattern labels
- Interpret charts and maps with AI and answer typed user questions
- Read the text and describe the shapes in an image with AI, and report whether each color, shape, and text item was verified
- Read AI responses and color identification results aloud with user-controlled speech playback
- Download enhanced images

## Required: Assumptions and dependencies

Conditions that you treat as true, and items that this project needs but does not build.

- A third party vision language model API remains available at an acceptable cost
- The server has an internet connection for AI interpretation
- The host firewall and network allow other LAN devices to reach port 9090
- Users have a current version of Chrome, Edge, Firefox, or Safari
- Users who rely on a screen reader supply their own, and the browser supplies the speech voices used for spoken playback
- Display color accuracy depends on device settings such as brightness and color temperature filters
- Published CVD simulation models are sufficiently accurate for the purposes of this application
- Each developer can install and run Docker on their machine

## Required: Out of scope

Behavior that the agent must not add.

- Native mobile applications
- Browser extensions
- Live camera mode and other video processing
- Personal calibration test or severity estimation
- User accounts, sign in, account deletion, and profile sync across devices
- Access from outside the LAN
- Medical diagnosis of CVD
- Offline operation of the portal
- A setting for a default enhancement method or overlay style
- Segmenting images with a machine learning model or with connected components for overlays
- Placing legend labels directly on chart regions
- Identifying the average color of a brushed region
- Sharing other than by browser download
- Separate image type classification or text recognition before the AI request
- A confirmation step before sending an image to the AI service, because AI runs only when the user clicks Explain
- A privacy notice or browser permission prompts
- Spoken input for questions
- Any guarantee that a verified item is correct, or use of results for medical, medication, or safety decisions

## Required: Requirements

Write one testable statement in each row. Add rows until the table lists every must-have function and quality. Do not leave a row half filled.

- Function rows use `SRS-FR-001`, `SRS-FR-002`, and so on.
- Quality rows (speed, security, reliability, usability) use `SRS-NFR-001`, `SRS-NFR-002`, and so on.
- Priority is `must` or `should`.
- Verification is behavior that you can see or measure and that proves the row.

| ID | Statement | Priority | Verification |
| --- | --- | --- | --- |
| SRS-FR-001 | The system shall allow the user to select an image using the browser file picker. (FR-1.1) | must | Selecting a PNG in the file picker uploads it and the image workspace shows the image. |
| SRS-FR-002 | The system shall allow the user to upload an image by drag and drop. (FR-1.2) | must | Dropping an image file on the upload control uploads it and the image workspace shows the image. |
| SRS-FR-003 | The system shall allow the user to paste an image from the clipboard. (FR-1.3) | should | Pasting a copied image on the home page uploads it and the image workspace shows the image. |
| SRS-FR-004 | The system shall accept PNG, JPEG, HEIC, and WEBP images. (FR-1.4) | must | One sample file of each format uploads successfully and renders in the image workspace. |
| SRS-FR-005 | The system shall convert embedded color profiles in uploaded images to sRGB. (Section 3.3) | must | A test image with an embedded Display P3 profile decodes to the expected sRGB pixel values. |
| SRS-FR-006 | The system shall downscale images larger than 12 megapixels for analysis while preserving the original for export. (FR-1.5) | must | For a 20 megapixel upload, the analysis image is at most 12 megapixels and the stored original keeps its 20 megapixel dimensions. |
| SRS-FR-007 | The system shall display an error message for unsupported or corrupted files. (FR-1.6) | must | Uploading a text file renamed as a PNG and a truncated JPEG each shows an error message, and the pipeline does not start. |
| SRS-FR-008 | The system shall automatically start the pipeline of decode, downscale, confusion detection, and enhancement after a successful upload and display the results. (FR-1.7) | must | With a profile set, a successful upload shows the enhanced result without any further user action. |
| SRS-FR-009 | If no CVD profile is set when an image is uploaded, the system shall ask the user to select one, including the no CVD option, before starting the pipeline. (FR-1.7, UC-1; inferred severe low-vision requirement) | must | With empty browser storage, an upload shows the profile prompt with the no CVD option, and the results appear after an option is selected. |
| SRS-FR-010 | The system shall automatically delete uploaded images and working copies after a configurable period, with a default of 24 hours. (Sections 2.5 and 7) | must | With a short test period, the files are gone from the server after expiry, and the default configuration value is 24 hours. |
| SRS-FR-011 | The system shall allow the user to select a CVD type (protan, deutan, tritan, or achromatopsia) or no CVD. (FR-2.1; inferred severe low-vision requirement) | must | The settings page offers all four types and no CVD, and a selected type is used in the next simulation. |
| SRS-FR-012 | The system shall allow the user to set severity from 0 to 1 using a slider, unless no CVD is selected. (FR-2.2; inferred severe low-vision requirement) | must | The slider reaches 0 and 1, the selected value is sent with the next request that needs the profile, and with no CVD selected the slider is disabled and no severity is sent. |
| SRS-FR-013 | The system shall store the active profile in browser storage and apply it to all features. (FR-2.3) | must | After a page reload, the profile is still selected, and simulation, enhancement, and color identification requests all carry it. |
| SRS-FR-014 | The system shall run confusion detection and enhancement again when the profile changes for a loaded image. (Section 3.4) | must | Changing the type from deutan to tritan on a loaded image updates the confusable pairs and the enhanced image. |
| SRS-FR-015 | The system shall simulate protan and deutan deficiencies using the Machado (2009) model with variable severity. (FR-3.1) | must | Output for a test image at several severities matches the reference values from the published model within the SRS-NFR-023 tolerance. |
| SRS-FR-016 | The system shall simulate tritan deficiency using the Brettel (1997) model. (FR-3.2) | must | Output for a test image matches the reference values from the published model within the SRS-NFR-023 tolerance. |
| SRS-FR-017 | The system shall simulate achromatopsia using luminance based conversion. (FR-3.3) | must | Output pixels have equal R, G, and B values that equal the computed luminance of the input pixel. |
| SRS-FR-018 | The system shall perform simulation in linear RGB space. (FR-3.4) | must | A unit test shows the input is linearized before the model is applied and re-encoded to sRGB after it, and the result matches the reference values. |
| SRS-FR-019 | The system shall display original and simulated images side by side or with a swipe slider. (FR-3.5) | must | The simulator page shows both images side by side or with a slider that reveals each one. |
| SRS-FR-020 | The system shall update a preview sized simulated image shortly after the user stops moving the severity slider. (FR-3.6) | should | Releasing the slider updates the preview with no further user action and no page reload. |
| SRS-FR-021 | The simulator page shall allow the user to select a CVD type and severity and display the simulated view of the loaded image. (Section 3.1, UC-6) | must | Opening the simulator from a loaded image and changing the type and severity changes the simulated view. |
| SRS-FR-022 | The system shall extract dominant colors using k-means clustering in CIELAB space. (FR-4.1) | must | For a flat graphic with known colors, the extracted palette contains a color within a small CIEDE2000 distance of each known color. |
| SRS-FR-023 | The system shall compute CIEDE2000 distances between dominant colors before and after simulation. (FR-4.2) | must | The distance function reproduces the published Sharma (2005) test pairs, and each detected pair reports both distances. |
| SRS-FR-024 | The system shall flag a pair as confusable when the simulated distance falls below a configurable threshold while the original distance exceeds it. (FR-4.3) | must | A red and green test pair under full deutan is flagged, a pair distinct under both views is not flagged, and changing the threshold changes the result. |
| SRS-FR-025 | The system shall produce a mask of pixels belonging to confusable colors. (FR-4.4) | must | For a flat graphic, the mask covers the pixels of the flagged colors and no pixels of the other colors. |
| SRS-FR-026 | The system shall display the list of confusable pairs with swatches, names, and patterns. (FR-4.5, UC-6) | should | The image workspace and the simulator page each list a test image's pairs, with swatches, names, and patterns. |
| SRS-FR-027 | The system shall inform the user when no confusable pairs are found. (FR-4.6) | must | An image with no confusable pairs under the active profile shows a message that no enhancement is needed. |
| SRS-FR-028 | The system shall modify only pixels within the confusion mask. (FR-5.1) | must | A pixel comparison of original and enhanced images finds no changed pixels outside the mask. |
| SRS-FR-029 | The system shall support one enhancement method, selected by technical evaluation from targeted daltonization, lightness separation, and hue rotation. (FR-5.2) | must | The evaluation result is recorded, and the system offers exactly that one method. |
| SRS-FR-030 | The system shall verify enhancement by re-running confusion detection on the result. (FR-5.3) | must | The pipeline output for a test image includes a confusable pair count from a detection run on the enhanced image. |
| SRS-FR-031 | The system shall allow the user to adjust enhancement strength. (FR-5.4) | should | Moving the strength control changes the enhanced image, and the change stays inside the mask. |
| SRS-FR-032 | The system shall allow the user to toggle between original and enhanced views. (FR-5.5) | must | The before and after slider in the image workspace shows the original and the enhanced image. |
| SRS-FR-033 | The system shall use the confusion mask to apply a distinct pattern (hatching, dots, crosshatch, or outline) to each confusable color group. (FR-6.3) | should | In a test image with two confusable groups, each group has a different pattern, and pixels outside the mask are unchanged. |
| SRS-FR-034 | The system shall allow the user to toggle overlays on and off. (FR-6.5) | should | The overlay control adds the patterns to the displayed image and removes them. |
| SRS-FR-035 | The system shall identify the color of a clicked or tapped point. (FR-7.1) | must | Clicking and tapping a known color region each returns that region's color. |
| SRS-FR-036 | The system shall return the nearest color name using CIEDE2000 against a bundled named color dataset. (FR-7.3) | must | Querying the exact value of a dataset color returns that color's name, with no network access. |
| SRS-FR-037 | The system shall display HEX, RGB, and HSL values and the basic color family. (FR-7.4) | must | Clicking a known color shows the correct HEX, RGB, and HSL values and color family. |
| SRS-FR-038 | The system shall show how the identified color appears under the active profile. (FR-7.5) | should | The color result shows a simulated swatch that changes when the profile changes. |
| SRS-FR-039 | The system shall announce identification results to screen readers using an ARIA live region. (FR-7.6) | must | After a click, the color name appears in an element with an `aria-live` attribute. |
| SRS-FR-040 | The system shall allow the user to download the enhanced image through the browser. (FR-8.1) | must | The download control saves a file that opens as the enhanced image. |
| SRS-FR-041 | The system shall export at the original image resolution. (FR-8.3) | should | The export of a 20 megapixel upload has the same pixel dimensions as the original. |
| SRS-FR-042 | When the user clicks Explain, the server shall send the image and its extracted color palette, with an ID for each color, and request structured output containing chart type, legend entries mapped to palette IDs, and a summary. (FR-9.4) | must | With a stubbed AI provider, the captured request has the image, the palette with IDs, and the output schema, and no request is sent before Explain is clicked. |
| SRS-FR-043 | The system shall validate each legend entry against the extracted palette and flag entries with a missing palette ID or a palette ID used by more than one entry. (FR-9.5) | must | Stubbed responses with a missing ID and a duplicated ID have those entries flagged, and a valid response has none flagged. |
| SRS-FR-044 | The system shall display a verified or unverified flag for each interpreted item, based on the result of the legend validation or, for shape and text items, the second AI read. (FR-9.6, UC-2; inferred severe low-vision requirement) | must | The AI panel shows a text flag of verified or unverified on each item, matching the validation result. |
| SRS-FR-045 | The system shall allow typed follow up questions, grounded in the same image context. (FR-9.7) | must | With a stubbed AI provider, a typed question produces a request with the same image and palette, and the answer appears in the AI panel. |
| SRS-FR-046 | The system shall show a clear message when the AI service is unavailable. (FR-9.9, UC-2) | must | With the provider unreachable, clicking Explain shows the message and the other features still work. |
| SRS-FR-047 | The system shall cache each AI interpretation by image and return the cached result for the same image. (UC-2, Section 7) | should | A second Explain on the same image returns the result without a new request to the stubbed provider. |
| SRS-FR-048 | The system shall expire cached interpretations after 30 days. (Section 7) | should | An entry dated 31 days ago is not returned, and the next Explain makes a new provider request. |
| SRS-FR-049 | The system shall provide all features without an account. (FR-12.2) | must | A new browser session uses every feature with no sign in page or prompt. |
| SRS-FR-050 | The system shall provide a keyboard- and screen-reader-navigable list of detected dominant colors and confusable pairs; each entry shall expose available color names and values, its pattern label, and its relationship to other entries. (FR-4.1, FR-4.5, FR-7.3, FR-7.4; inferred low-vision requirement) | must | Using only the keyboard and a screen reader, a tester can navigate detected colors and pairs and hear their names, values, pattern labels, and pair relationships. |
| SRS-FR-051 | The system shall expose AI chart type, legend entries, summary, follow-up answers, and each item's verified or unverified state as semantically structured text available to screen readers. (FR-9.4, FR-9.6, FR-9.7, NFR-4.1; inferred low-vision requirement) | must | A screen reader announces the AI result content and the matching verified or unverified state for each interpreted item. |
| SRS-FR-052 | The system shall provide keyboard-accessible controls to start, pause or resume, and stop spoken playback of AI responses and color identification results, including the verified or unverified states of AI items. (FR-7.6, FR-9.6, NFR-4.1; inferred low-vision requirement) | must | With speech output enabled, keyboard operation starts, pauses or resumes, and stops playback of an AI response and of a color result; the spoken AI content includes each item's verification state. |
| SRS-FR-053 | The portal shall include an introduction that explains CVD profiles and enhancement. (Section 2.6) | should | A new user can open the introduction in the portal and read both explanations. |
| SRS-FR-054 | With no CVD selected, the system shall skip confusable pair flagging and enhancement, show the original image, and still provide the color list, color identification, and AI interpretation. (FR-1.7, FR-2.1; inferred severe low-vision requirement) | must | With no CVD selected, an upload shows the original image and the color list with no enhanced image, and color identification and Explain both work. |
| SRS-FR-055 | When the user clicks Explain, the system shall return each piece of text the AI service reads in the image as a separate item, with its location in the image, in reading order. (FR-9.4; inferred severe low-vision requirement) | must | With a stubbed AI provider, the request schema asks for text items, and the AI panel lists each returned item with its location, in reading order. |
| SRS-FR-056 | When the user clicks Explain, the system shall return each distinct shape the AI service finds in the image as a separate item, with its kind, its location, and the palette ID of its color. (FR-9.4; inferred severe low-vision requirement) | must | With a stubbed AI provider, the request schema asks for shape items, and the AI panel lists each returned item with its kind, location, and color name. |
| SRS-FR-057 | The system shall check text and shape items with a second, separate AI read of the image, and shall flag an item as verified only when both reads agree on it. (FR-9.5, FR-9.6; inferred severe low-vision requirement) | must | With a stubbed provider, one Explain makes two reads, items that match are flagged verified, items that differ or appear in one read are flagged unverified, and both reads count toward the rate limit and spend cap. |
| SRS-FR-058 | The system shall take the name and values of each color item from its palette entry and the bundled named color dataset, not from the AI text, and shall flag a color item as unverified when it has no valid palette ID. (FR-7.3, FR-9.5; inferred severe low-vision requirement) | must | With a stubbed response that calls a palette color by the wrong name, the panel shows the dataset name; an item with an invalid palette ID is flagged unverified. |
| SRS-FR-059 | Each follow up answer shall cite the interpreted items it relies on, and the system shall flag the answer as verified only when every cited item is verified. (FR-9.6, FR-9.7; inferred severe low-vision requirement) | must | Stubbed answers citing only verified items are flagged verified; answers citing an unverified item or no items are flagged unverified. |
| SRS-FR-060 | The AI panel shall explain in text what each flag means, including that a verified color was checked against the image's pixels, that verified text or a verified shape means two AI reads agreed, and that neither guarantees correctness. (FR-9.6; inferred severe low-vision requirement) | must | The explanation is reachable by keyboard from the AI panel, and a screen reader announces all three points. |
| SRS-FR-061 | The system shall allow the user to move an identification point across the image using the keyboard, and shall announce the color at the point after each move. (FR-7.1, FR-7.6; inferred severe low-vision requirement) | must | Using only the arrow keys, a tester moves the point onto a known color region and the color name appears in the `aria-live` element. |
| SRS-FR-062 | The system shall announce the start and the completion or failure of an upload, the pipeline, and each AI request to screen readers, without moving keyboard focus. (FR-1.6, FR-1.7, FR-9.9, NFR-4.1; inferred severe low-vision requirement) | must | During an upload and an Explain, each message appears in an `aria-live` element and focus stays on the same control, including when the request fails. |
| SRS-FR-063 | The system shall let the user set speech rate and turn on automatic reading of new results, off by default so that speech does not overlap a screen reader, and shall keep these settings in browser storage. (NFR-4.1; inferred severe low-vision requirement) | should | With automatic reading off, a new result is not spoken; with it on, the result is spoken without further action at the set rate; both settings survive a page reload. |
| SRS-FR-064 | Each image in the portal shall have a text alternative that states which view it shows and, once an interpretation exists, its summary. (NFR-4.1; inferred severe low-vision requirement) | must | A screen reader announces the view name for each image, and the summary after Explain completes. |
| SRS-NFR-001 | Simulation and enhancement of a preview sized image of up to 2 megapixels shall complete in under 1 second on the reference host. (NFR-1.1) | should | A timing test on a 2 megapixel image in the reference container reports under 1 second. |
| SRS-NFR-002 | A 12 megapixel export shall complete in under 5 seconds on the reference host. (NFR-1.1) | should | A timing test on a 12 megapixel export in the reference container reports under 5 seconds. |
| SRS-NFR-003 | Confusion detection shall complete in under 500 milliseconds on a downscaled image on the reference host. (NFR-1.2) | should | A timing test of detection on a downscaled image in the reference container reports under 500 milliseconds. |
| SRS-NFR-004 | AI interpretation, including the second read of shape and text items, shall return a result within 30 seconds under normal network conditions. (NFR-1.4; inferred severe low-vision requirement) | should | Timed Explain requests against the real provider on a normal connection each return with verification flags within 30 seconds. |
| SRS-NFR-005 | The home page shall become interactive within 2 seconds on the LAN in the reference browser. (NFR-1.5) | must | Chrome performance profiling from a second LAN device reports time to interactive under 2 seconds. |
| SRS-NFR-006 | Traffic between the server and the AI provider shall use HTTPS with TLS 1.2 or later. (NFR-2.1) | must | The configured provider URL is `https`, and the client rejects connections below TLS 1.2. |
| SRS-NFR-007 | API keys for third party services shall reside only on the server. (NFR-2.2) | must | A search of browser delivered assets and API responses finds no API key. |
| SRS-NFR-008 | The server shall validate all inputs. (NFR-2.3) | must | Requests with invalid IDs, profile values, and coordinates each receive a client error response and do not cause a server error. |
| SRS-NFR-009 | The server shall limit image upload size to 10 MB. (NFR-2.3) | must | An upload over 10 MB is rejected with an error message, and a 10 MB upload is accepted. |
| SRS-NFR-010 | The server shall rate limit AI requests per browser session and IP address. (NFR-2.4) | must | Requests past the configured limit from one session, and from one IP address, are refused, and no provider call is made. |
| SRS-NFR-011 | The server shall stop AI requests when a configurable global spend cap is reached. (NFR-2.4, UC-2) | must | With a low test cap, the request past the cap makes no provider call, and the user sees that AI is temporarily unavailable. |
| SRS-NFR-012 | All interactive elements and dynamic results shall expose accessible names, roles, states, and updates to screen readers. (NFR-4.1; extended for low-vision access) | must | axe reports no missing label violations on any page, and a screen reader walkthrough completes the enhance and interpret tasks and announces updated results. |
| SRS-NFR-013 | All pages shall remain usable at 200 percent browser zoom. (NFR-4.2) | must | At 200 percent zoom, each page's controls are visible and operable, and the enhance task completes. |
| SRS-NFR-014 | The portal shall never use color, shape, pattern, or position as the only means of conveying information. (NFR-4.3; extended for low-vision access) | must | A grayscale and screen-reader review finds that each status, flag, pattern, and control state remains distinguishable and has a text equivalent. |
| SRS-NFR-015 | Text and interface elements shall meet WCAG 2.2 AA contrast ratios. (NFR-4.4) | must | axe reports no contrast violations on any page. |
| SRS-NFR-016 | All pages shall work at phone and computer screen widths. (Section 3.1) | must | Playwright runs of the enhance task pass at a phone viewport and a computer viewport, with no horizontal page scroll. |
| SRS-NFR-017 | A first time user with a profile set shall be able to enhance an image within 3 clicks of the home page. (NFR-4.5) | must | A Playwright run from the home page reaches the enhanced result in 3 clicks or fewer, and the user study confirms it. |
| SRS-NFR-018 | The portal shall achieve a System Usability Scale score of 70 or higher in user testing. (NFR-4.6) | should | The mean SUS score from the task based user study is 70 or higher. |
| SRS-NFR-019 | The portal shall recover from AI or network failures without losing the current results. (NFR-5.2) | must | After a failed Explain, the enhanced image and confusable pairs remain on screen and the next request works. |
| SRS-NFR-020 | All features except AI interpretation shall work when the server has no internet connection. (Section 2.4) | must | With server internet access blocked, upload, simulation, enhancement, color identification, and export all complete. |
| SRS-NFR-021 | At least 99 percent of sessions during beta testing shall complete without a server error. (NFR-5.3) | should | Server logs from beta testing show at least 99 percent of sessions with no 5xx response. |
| SRS-NFR-022 | The portal shall target 99 percent availability on the LAN host during the evaluation period. (NFR-5.4) | should | Periodic health checks during the evaluation period succeed at least 99 percent of the time. |
| SRS-NFR-023 | The Python simulation output shall match an independent reference implementation, such as the DaltonLens package, with a mean per pixel difference under 1 percent. (NFR-6.1) | must | A unit test comparing output with the reference implementation on test images reports a mean per pixel difference under 1 percent. |
| SRS-NFR-024 | Targeted enhancement shall reduce confusable pairs by at least 80 percent on the flat graphics test dataset. (NFR-6.2) | should | The before and after confusable pair counts over the dataset show a reduction of at least 80 percent. |
| SRS-NFR-025 | AI legend mapping shall be at least 90 percent correct on the labeled chart test set. (NFR-6.3) | should | A comparison with the labeled ground truth reports at least 90 percent of legend entries correct. |
| SRS-NFR-026 | Users shall achieve higher task accuracy with ChromaSense than with the original image or a global daltonization filter. (Section 8) | should | The study's task accuracy for ChromaSense is higher than for each of the two baselines. |
| SRS-NFR-027 | The color engine shall be a separate Python package. (NFR-7.1) | must | The package installs and its tests run on their own, without the rest of the application. |
| SRS-NFR-028 | Unit tests shall cover at least 70 percent of the color engine code. (NFR-7.1) | must | The coverage report for the package shows at least 70 percent. |
| SRS-NFR-029 | The codebase shall follow the architecture documented in `architecture.md`. (NFR-7.2) | must | A review or import check finds no source dependency that breaks the rules in `architecture.md`. |
| SRS-NFR-030 | The codebase shall follow consistent style rules. (NFR-7.2) | must | The configured linter and formatter checks pass on the whole codebase. |
| SRS-NFR-031 | Every pull request shall pass automated builds and tests before merging. (NFR-7.3) | must | A pull request with a failing test shows a failed required check and cannot be merged. |
| SRS-NFR-032 | The color engine shall not depend on the web framework. (NFR-7.4) | must | The color engine's tests pass in an environment where the web framework is not installed. |
| SRS-NFR-033 | The portal shall listen on port 9090 on all host interfaces and be reachable at `http://<host-ip>:9090` from another device on the same LAN. (NFR-8.1) | must | A second computer and a phone on the LAN each open that address and upload an image. |
| SRS-NFR-034 | The project repository shall include a README and setup guide that explain how to start the portal and reach it from another device on the LAN. (Section 2.6) | should | A developer who follows only the guide starts the portal and reaches it from a second LAN device. |
| SRS-NFR-035 | The portal shall respect browser or operating-system forced-colors settings while preserving readable text, visible focus, and distinguishable controls and status states. (NFR-4.3, NFR-4.4; inferred low-vision requirement) | must | With forced-colors mode enabled, text, focus indicators, controls, and status states remain visible and distinguishable during keyboard navigation. |
| SRS-NFR-036 | Every function of the portal shall be operable using only the keyboard, including upload, sliders, and the before and after view, with visible focus and no keyboard trap. (NFR-4.1; inferred severe low-vision requirement) | must | A keyboard-only run with no pointer completes the upload, profile, enhance, identify, Explain, and playback tasks, and focus is visible at each stop. |
| SRS-NFR-037 | All pages shall reflow without loss of content or function at 400 percent browser zoom on a 1280 pixel wide window. (NFR-4.2; inferred severe low-vision requirement) | must | At 400 percent zoom, each page has no horizontal page scroll, and the enhance and Explain tasks complete. |
| SRS-NFR-038 | A user with no view of the screen shall be able to upload an image, set the profile, and get every color, shape, and text item with its flag. (NFR-4.1; inferred severe low-vision requirement) | must | With the display off, a tester using NVDA on Windows, and another using VoiceOver on a phone, completes the task and correctly reports the items in a test image and their flags. |
| SRS-NFR-039 | AI text and shape items shall each be at least 90 percent correct on a labeled test set of charts, maps, and flat graphics. (NFR-6.3; inferred severe low-vision requirement) | should | A comparison with the labeled ground truth reports at least 90 percent of text items and of shape items correct. |
| SRS-NFR-040 | At least 95 percent of text and shape items flagged verified shall be correct on the labeled test set. (NFR-6.3; inferred severe low-vision requirement) | should | A comparison of the verified items with the labeled ground truth reports at least 95 percent correct. |

## Optional: External interfaces

Inputs and outputs that cross the software boundary, if the product perspective does not cover them.

**User interface screens**

- Home page: image upload control and a link to the simulator
- Image workspace: before and after slider, controls for enhancement strength, overlays, and AI interpretation, a click and keyboard color picker, and speech playback controls
- Simulator page: CVD type selector and severity slider
- AI panel: interpretation summary, legend mapping, text and shape items, verified or unverified flags with an explanation of their meaning, a text question field, and speech playback controls
- Settings page: CVD profile, including no CVD, and speech rate and automatic reading

**Communication**

- Browsers reach the portal over HTTP on port 9090. Plain HTTP is permitted on the LAN for this release.
- Calls from the server to the AI provider use HTTPS with TLS 1.2 or later.
- The server exposes a REST API with JSON payloads, plus multipart upload and image responses.
- Requests are not authenticated. The browser sends the CVD profile with each request that needs it.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/images` | Upload an image and start the pipeline |
| POST | `/api/images/{id}/analyze` | Run confusion detection and enhancement again for a changed profile |
| GET | `/api/images/{id}/render` | Return a preview of the original, simulated, enhanced, or overlaid image |
| GET | `/api/images/{id}/color` | Return color information for a clicked point |
| GET | `/api/images/{id}/export` | Download the enhanced image at original resolution |
| POST | `/api/interpret` | Return AI chart or map interpretation |
| POST | `/api/ask` | Answer a question about an interpreted image |

## Optional: Logical data

Data that the software must store, in business terms.

- CVD profile: the CVD type or no CVD, severity, and time of last update, kept in the user's browser
- Speech settings: the speech rate and the automatic reading setting, kept in the user's browser
- Temporary image: the uploaded original, its working copy, a hash that identifies the image, and its creation and expiry times, kept on the server for 24 hours by default
- Interpretation: the image hash, summary, legend mapping, text and shape items, verification flags, and creation time, cached on the server for 30 days
- AI usage: the request count and estimated cost for each period and browser session, kept on the server
- Named color: the name, HEX value, CIELAB values, and basic color family of each color in the dataset bundled with the server

## Optional: Performance

Response time, volume, or rate. For each number here, add a matching `SRS-NFR-` row.

The reference host is a Docker container limited to 4 CPU cores and 8 GB of memory. The reference browser is the current version of Chrome.

- Preview simulation and enhancement, up to 2 megapixels: under 1 second (SRS-NFR-001, provisional until measured on the reference host)
- 12 megapixel export: under 5 seconds (SRS-NFR-002, provisional until measured on the reference host)
- Confusion detection on a downscaled image: under 500 milliseconds (SRS-NFR-003, provisional until measured on the reference host)
- AI interpretation: within 30 seconds (SRS-NFR-004, provisional until measured with the chosen provider)
- Home page interactive on the LAN: within 2 seconds (SRS-NFR-005)

## Optional: Design constraints

Constraints from the requirements (a required protocol, a regulation, a platform that you cannot leave). Stack and architecture choices go in `architecture.md`.

- All image processing must be written in Python 3.11 or later and run on the server.
- The portal must run in Docker on a server host on the LAN.
- The team development environment must be Docker Compose with a dev container committed to the repository.
- The portal must listen on port 9090.
- The portal has no login, so it must not be exposed to the internet in this release.
- LLM API keys must be stored on the server and never sent to the browser.
- All pages must follow WCAG 2.2 AA.
- The project must be completed within the course semester by a team of three.

## Optional: Software attributes

Qualities that do not already have an `SRS-NFR-` row.

none
