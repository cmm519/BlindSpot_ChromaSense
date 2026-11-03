# Software Requirements Specification

**ChromaSense: AI Powered Color Accessibility Web Portal**

Version 2.1

**Team BlindSpot**

- Sapnil Basnet
- Shivendra Bhagat
- Corbin Copper

Software Engineering Project  
Department of Computer Science, Texas State University  
November 2026

## Revision History

| Version | Date | Description | Authors |
|---|---|---|---|
| 1.0 | September 2026 | Initial SRS submission (native iOS application) | Team BlindSpot |
| 2.0 | November 2026 | Changed the platform to a server-side web portal on the LAN, removed the privacy requirements, and reduced the v1.0 release scope | Team BlindSpot |
| 2.1 | November 2026 | Recorded the first architecture decision: Clean Architecture and Pipe and Filter | Team BlindSpot |

## Table of Contents

- [1. Introduction](#1-introduction)
  - [1.1 Purpose](#11-purpose)
  - [1.2 Scope](#12-scope)
  - [1.3 Definitions, Acronyms, and Abbreviations](#13-definitions-acronyms-and-abbreviations)
  - [1.4 References](#14-references)
  - [1.5 Document Overview](#15-document-overview)
- [2. Overall Description](#2-overall-description)
  - [2.1 Product Perspective](#21-product-perspective)
  - [2.2 Product Functions](#22-product-functions)
  - [2.3 User Classes and Characteristics](#23-user-classes-and-characteristics)
  - [2.4 Operating Environment](#24-operating-environment)
  - [2.5 Design and Implementation Constraints](#25-design-and-implementation-constraints)
  - [2.6 User Documentation](#26-user-documentation)
  - [2.7 Assumptions and Dependencies](#27-assumptions-and-dependencies)
- [3. External Interface Requirements](#3-external-interface-requirements)
  - [3.1 User Interfaces](#31-user-interfaces)
  - [3.2 Hardware Interfaces](#32-hardware-interfaces)
  - [3.3 Software Interfaces](#33-software-interfaces)
  - [3.4 Communication Interfaces](#34-communication-interfaces)
- [4. Functional Requirements](#4-functional-requirements)
  - [4.1 Image Input (F1)](#41-image-input-f1)
  - [4.2 CVD Profile Management (F2, F12)](#42-cvd-profile-management-f2-f12)
  - [4.3 CVD Simulation (F3)](#43-cvd-simulation-f3)
  - [4.4 Confusion Detection (F4)](#44-confusion-detection-f4)
  - [4.5 Targeted Enhancement (F5)](#45-targeted-enhancement-f5)
  - [4.6 Pattern Overlays (F10)](#46-pattern-overlays-f10)
  - [4.7 Color Identification (F6)](#47-color-identification-f6)
  - [4.8 Export (F7)](#48-export-f7)
  - [4.9 AI Chart and Map Interpreter (F8, F9)](#49-ai-chart-and-map-interpreter-f8-f9)
  - [4.10 Personal Calibration Test (F11)](#410-personal-calibration-test-f11)
  - [4.11 Live Camera Mode (F14)](#411-live-camera-mode-f14)
  - [4.12 Accounts and Authentication](#412-accounts-and-authentication)
- [5. Non Functional Requirements](#5-non-functional-requirements)
  - [5.1 Performance](#51-performance)
  - [5.2 Security](#52-security)
  - [5.3 Privacy](#53-privacy)
  - [5.4 Usability and Accessibility](#54-usability-and-accessibility)
  - [5.5 Reliability and Availability](#55-reliability-and-availability)
  - [5.6 Accuracy](#56-accuracy)
  - [5.7 Maintainability and Portability](#57-maintainability-and-portability)
  - [5.8 Deployment and Network](#58-deployment-and-network)
- [6. Use Cases](#6-use-cases)
  - [6.1 UC-1: Enhance an Image](#61-uc-1-enhance-an-image)
  - [6.2 UC-2: Interpret a Chart](#62-uc-2-interpret-a-chart)
  - [6.3 UC-3: Identify a Color](#63-uc-3-identify-a-color)
  - [6.4 UC-4: Take the Calibration Test](#64-uc-4-take-the-calibration-test)
  - [6.5 UC-5: Use Live Camera Mode](#65-uc-5-use-live-camera-mode)
  - [6.6 UC-6: Simulate CVD for Content Review](#66-uc-6-simulate-cvd-for-content-review)
- [7. Data Requirements](#7-data-requirements)
- [8. Acceptance Criteria and Verification](#8-acceptance-criteria-and-verification)
- [9. Requirements Traceability Matrix](#9-requirements-traceability-matrix)
- [Appendix A: Out of Scope Items](#appendix-a-out-of-scope-items)
- [Appendix B: Deferred and Removed Requirements](#appendix-b-deferred-and-removed-requirements)
- [Appendix C: Architecture Decisions](#appendix-c-architecture-decisions)

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the functional and non functional requirements for ChromaSense, a server-side web portal developed by Team BlindSpot. The document serves as the agreed reference for design, implementation, testing, and evaluation, and is intended for the development team, the course instructor, and any testers or stakeholders.

### 1.2 Scope

ChromaSense helps people with color vision deficiency (CVD) understand color coded information in images. Unlike global color filters, the system detects which colors are confusable for a specific user, enhances only those colors, and uses AI to explain the meaning of color coded content such as charts, maps, and legends. The portal also includes a CVD simulator for people with normal color vision.

A user opens the portal from a browser on the local network and uploads an image, which starts the processing pipeline. The system consists of a browser client and a Python server that handles image processing and AI interpretation. Charts, maps, and flat graphics are the supported target for this release, and photographs are handled on a best effort basis. Native mobile applications and browser extensions are outside the scope of this release.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|---|---|
| CVD | Color vision deficiency, commonly called color blindness |
| Protan | Reduced or absent sensitivity to red light (protanomaly, protanopia) |
| Deutan | Reduced or absent sensitivity to green light (deuteranomaly, deuteranopia) |
| Tritan | Reduced or absent sensitivity to blue light (tritanomaly, tritanopia) |
| Achromatopsia | Complete or near complete absence of color vision |
| Severity | A value from 0 to 1 describing the degree of a CVD, where 1 is full dichromacy |
| Confusable pair | Two colors that are distinct to typical vision but nearly indistinguishable to a given CVD profile |
| Daltonization | A technique that shifts color information lost to a CVD into channels the user can perceive |
| CIELAB | A perceptually based color space used for color difference calculations |
| CIEDE2000 | The standard formula for perceptual color difference (Delta E) |
| VLM | Vision language model, an AI model that accepts images and text |
| SRS | Software Requirements Specification |
| FR / NFR | Functional requirement / Non functional requirement |
| MVP | Minimum viable product |
| LAN | Local area network |
| Pipeline | The server processing sequence that starts after an upload: decode, downscale, confusion detection, enhancement, and result display |
| Dev container | A container definition committed to the repository that gives each developer the same tools and libraries |

### 1.4 References

- IEEE Std 830-1998 and ISO/IEC/IEEE 29148:2018, Recommended practice and standard for software requirements specifications.
- Machado, G. M., Oliveira, M. M., and Fernandes, L. A. F. (2009). A Physiologically based Model for Simulation of Color Vision Deficiency. IEEE Transactions on Visualization and Computer Graphics.
- Brettel, H., Viénot, F., and Mollon, J. D. (1997). Computerized simulation of color appearance for dichromats. Journal of the Optical Society of America A.
- Sharma, G., Wu, W., and Dalal, E. N. (2005). The CIEDE2000 color difference formula: Implementation notes. Color Research and Application.
- W3C. Web Content Accessibility Guidelines (WCAG) 2.2.
- Team BlindSpot. ChromaSense Project Description, Version 3.0.

### 1.5 Document Overview

Section 2 describes the product context, users, environment, and constraints. Section 3 lists external interface requirements. Section 4 specifies functional requirements by feature. Section 5 specifies non functional requirements. Section 6 presents use cases. Section 7 defines the data requirements. Section 8 lists acceptance criteria and verification methods, and Section 9 contains the traceability matrix. Appendix B records the requirements deferred or removed since Version 1.0, and Appendix C records architecture decisions.

Requirement IDs from Version 1.0 are kept stable, so gaps in the numbering are expected. Each missing ID is listed in Appendix B.

## 2. Overall Description

### 2.1 Product Perspective

ChromaSense is a new, self contained product. It replaces the general purpose approach of global color filters with content aware assistance. The major subsystems are listed below.

| Subsystem | Location | Responsibility |
|---|---|---|
| Browser client | Browser | Upload control, before and after slider, color picker, profile storage, results display |
| Web application | Server (FastAPI) | Serves pages and the API, validates input, rate limits AI requests, runs on port 9090 |
| Color engine | Server (Python package) | CVD simulation, confusion detection, targeted enhancement, pattern overlays, color naming |
| Worker pool | Server | Runs CPU heavy pipeline work outside the web request handler, with a concurrency cap |
| Temporary image store | Server | Holds uploaded originals and working copies until they expire |
| AI interpretation service | Server | Chart and map interpretation, visual Q&A, output validation |
| Database | Server (SQLite) | Cached interpretations and AI usage counters |

### 2.2 Product Functions

- Upload images from a file picker, by drag and drop, or from the clipboard, which starts the pipeline.
- Select a CVD profile with type and severity.
- Simulate how an image appears to each CVD type.
- Detect confusable color pairs for the active profile.
- Enhance only confusable colors.
- Add pattern overlays to confusable colors.
- Identify the name and values of a clicked color.
- Interpret charts and maps with AI and answer typed user questions.
- Download enhanced images.

### 2.3 User Classes and Characteristics

| User Class | Characteristics | Primary Features |
|---|---|---|
| Users with CVD | Varying CVD type and severity, general web browsing skills | Enhancement, overlays, color identification, AI interpreter |
| Students and professionals with CVD | Frequently read charts, maps, and dashboards | AI interpreter, visual Q&A, overlays |
| Designers, educators, developers | Typical color vision, want to test content | Simulator, confusion detection |
| General public | Curious about CVD | Simulator |

### 2.4 Operating Environment

- Current versions of Chrome, Edge, Firefox, or Safari on a computer or phone connected to the same LAN as the server.
- A server host on the LAN running the portal in Docker, using Python 3.11 or later.
- The server needs an internet connection only for AI interpretation.

### 2.5 Design and Implementation Constraints

- All image processing must be written in Python and run on the server.
- The team development environment must be Docker Compose with a dev container committed to the repository.
- The portal must listen on port 9090.
- The portal has no login, so it must not be exposed to the internet in this release.
- LLM API keys must be stored on the server and never sent to the browser.
- Uploaded images and working copies must be deleted automatically after a configurable period, with a default of 24 hours.
- The project must be completed within the course semester by a team of three.

### 2.6 User Documentation

- In portal introduction that explains CVD profiles and enhancement.
- README and setup guide in the project repository, including how to start the portal and reach it from another device on the LAN.

### 2.7 Assumptions and Dependencies

- A third party vision language model API remains available at an acceptable cost.
- The host firewall and network allow other LAN devices to reach port 9090.
- Display color accuracy depends on device settings such as brightness and color temperature filters.
- Published CVD simulation models are sufficiently accurate for the purposes of this application.
- Each developer can install and run Docker on their machine.

## 3. External Interface Requirements

### 3.1 User Interfaces

- Home page with an image upload control and a link to the simulator.
- Image workspace with a before and after slider, controls for enhancement strength, overlays, and AI interpretation, and a click to identify color picker.
- Simulator page with CVD type selector and severity slider.
- AI panel showing the interpretation summary, legend mapping, verified or unverified flags, and a text question field.
- Settings page for the CVD profile.
- All pages follow WCAG 2.2 AA and must never rely on color alone to convey information.
- All pages must work at phone and computer screen widths.

### 3.2 Hardware Interfaces

The portal has no direct hardware interfaces. The server runs on a standard LAN host, and the browser uses the host device's display and input.

### 3.3 Software Interfaces

| Interface | Purpose |
|---|---|
| FastAPI | Web application and REST API |
| Python imaging libraries with HEIC support | Decode uploads, convert embedded color profiles to sRGB, encode results |
| Python numerical libraries | Color conversion, clustering, simulation, enhancement |
| Vision language model API | Chart and map interpretation, accessed only by the server |
| SQLite | Server side persistence |
| Browser storage | Saves the CVD profile in the user's browser |

### 3.4 Communication Interfaces

- Browsers reach the portal over HTTP on port 9090. Plain HTTP is permitted on the LAN for this release.
- Calls from the server to the AI provider use HTTPS with TLS 1.2 or later.
- The server exposes a REST API with JSON payloads, plus multipart upload and image responses.
- Requests are not authenticated. The browser sends the CVD profile with each request that needs it.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/images` | Upload an image and start the pipeline |
| POST | `/api/images/{id}/analyze` | Run confusion detection and enhancement again for a changed profile |
| GET | `/api/images/{id}/render` | Return a preview of the original, simulated, enhanced, or overlaid image |
| GET | `/api/images/{id}/color` | Return color information for a clicked point |
| GET | `/api/images/{id}/export` | Download the enhanced image at original resolution |
| POST | `/api/interpret` | Return AI chart or map interpretation |
| POST | `/api/ask` | Answer a question about an interpreted image |

## 4. Functional Requirements

Priority levels: High requirements form the MVP, Medium requirements are core differentiators, and Low requirements are enhancements that may be deferred.

### 4.1 Image Input (F1)

| ID | Requirement | Priority |
|---|---|---|
| FR-1.1 | The system shall allow the user to select an image using the browser file picker. | High |
| FR-1.2 | The system shall allow the user to upload an image by drag and drop. | High |
| FR-1.3 | The system shall allow the user to paste an image from the clipboard. | Medium |
| FR-1.4 | The system shall accept PNG, JPEG, HEIC, and WEBP images. | High |
| FR-1.5 | The system shall downscale images larger than 12 megapixels for analysis while preserving the original for export. | High |
| FR-1.6 | The system shall display an error message for unsupported or corrupted files. | High |
| FR-1.7 | The system shall automatically start the pipeline after a successful upload and display the results. If no CVD profile is set, the system shall first ask the user to select one. | High |

### 4.2 CVD Profile Management (F2, F12)

| ID | Requirement | Priority |
|---|---|---|
| FR-2.1 | The system shall allow the user to select a CVD type: protan, deutan, tritan, or achromatopsia. | High |
| FR-2.2 | The system shall allow the user to set severity from 0 to 1 using a slider. | High |
| FR-2.3 | The system shall store the active profile in browser storage and apply it to all features. | High |

### 4.3 CVD Simulation (F3)

| ID | Requirement | Priority |
|---|---|---|
| FR-3.1 | The system shall simulate protan and deutan deficiencies using the Machado (2009) model with variable severity. | High |
| FR-3.2 | The system shall simulate tritan deficiency using the Brettel (1997) model. | High |
| FR-3.3 | The system shall simulate achromatopsia using luminance based conversion. | High |
| FR-3.4 | The system shall perform simulation in linear RGB space. | High |
| FR-3.5 | The system shall display original and simulated images side by side or with a swipe slider. | High |
| FR-3.6 | The system shall update a preview sized simulated image shortly after the user stops moving the severity slider. | Medium |

### 4.4 Confusion Detection (F4)

Charts, maps, and flat graphics are the supported target for these requirements. Photographs are processed on a best effort basis.

| ID | Requirement | Priority |
|---|---|---|
| FR-4.1 | The system shall extract dominant colors using k-means clustering in CIELAB space. | High |
| FR-4.2 | The system shall compute CIEDE2000 distances between dominant colors before and after simulation. | High |
| FR-4.3 | The system shall flag a pair as confusable when the simulated distance falls below a configurable threshold while the original distance exceeds it. | High |
| FR-4.4 | The system shall produce a mask of pixels belonging to confusable colors. | High |
| FR-4.5 | The system shall display the list of confusable pairs with swatches, names, and patterns. | Medium |
| FR-4.6 | The system shall inform the user when no confusable pairs are found. | High |

### 4.5 Targeted Enhancement (F5)

| ID | Requirement | Priority |
|---|---|---|
| FR-5.1 | The system shall modify only pixels within the confusion mask. | High |
| FR-5.2 | The system shall support one enhancement method, selected by technical evaluation from targeted daltonization, lightness separation, and hue rotation. | High |
| FR-5.3 | The system shall verify enhancement by re-running confusion detection on the result. | High |
| FR-5.4 | The system shall allow the user to adjust enhancement strength. | Medium |
| FR-5.5 | The system shall allow the user to toggle between original and enhanced views. | High |

### 4.6 Pattern Overlays (F10)

| ID | Requirement | Priority |
|---|---|---|
| FR-6.3 | The system shall use the confusion mask to apply a distinct pattern (hatching, dots, crosshatch, or outline) to each confusable color group. | Medium |
| FR-6.5 | The system shall allow the user to toggle overlays on and off. | Medium |

### 4.7 Color Identification (F6)

| ID | Requirement | Priority |
|---|---|---|
| FR-7.1 | The system shall identify the color of a clicked or tapped point. | High |
| FR-7.3 | The system shall return the nearest color name using CIEDE2000 against a bundled named color dataset. | High |
| FR-7.4 | The system shall display HEX, RGB, and HSL values and the basic color family. | High |
| FR-7.5 | The system shall show how the identified color appears under the active profile. | Medium |
| FR-7.6 | The system shall announce identification results to screen readers using an ARIA live region. | High |

### 4.8 Export (F7)

| ID | Requirement | Priority |
|---|---|---|
| FR-8.1 | The system shall allow the user to download the enhanced image through the browser. | High |
| FR-8.3 | The system shall export at the original image resolution. | Medium |

### 4.9 AI Chart and Map Interpreter (F8, F9)

| ID | Requirement | Priority |
|---|---|---|
| FR-9.4 | When the user clicks Explain, the server shall send the image and its extracted color palette, with an ID for each color, and request structured output containing chart type, legend entries mapped to palette IDs, and a summary. | Medium |
| FR-9.5 | The system shall validate each legend entry against the extracted palette and flag entries with a missing palette ID or a palette ID used by more than one entry. | Medium |
| FR-9.6 | The system shall display a verified or unverified flag for each interpreted item, based on the result of FR-9.5. | Medium |
| FR-9.7 | The system shall allow typed follow up questions, grounded in the same image context. | Medium |
| FR-9.9 | The system shall show a clear message when the AI service is unavailable. | High |

### 4.10 Personal Calibration Test (F11)

Deferred. See Appendix B.

### 4.11 Live Camera Mode (F14)

Deferred. See Appendix B.

### 4.12 Accounts and Authentication

| ID | Requirement | Priority |
|---|---|---|
| FR-12.2 | The system shall provide all features without an account. | High |

## 5. Non Functional Requirements

### 5.1 Performance

The reference host is a Docker container limited to 4 CPU cores and 8 GB of memory, and the reference browser is the current version of Chrome. The numbers in NFR-1.1 and NFR-1.2 are provisional until measured on the reference host.

| ID | Requirement |
|---|---|
| NFR-1.1 | Simulation and enhancement of a preview sized image of up to 2 megapixels shall complete in under 1 second, and a 12 megapixel export shall complete in under 5 seconds, on the reference host. |
| NFR-1.2 | Confusion detection shall complete in under 500 milliseconds on a downscaled image on the reference host. |
| NFR-1.4 | AI interpretation shall return a result within 8 seconds under normal network conditions. |
| NFR-1.5 | The home page shall become interactive within 2 seconds on the LAN in the reference browser. |

### 5.2 Security

| ID | Requirement |
|---|---|
| NFR-2.1 | Traffic between the server and the AI provider shall use HTTPS with TLS 1.2 or later. |
| NFR-2.2 | API keys for third party services shall reside only on the server. |
| NFR-2.3 | The server shall validate all inputs and limit image upload size to 10 MB. |
| NFR-2.4 | The server shall rate limit AI requests per browser session and IP address, and shall stop AI requests when a configurable global spend cap is reached. |

### 5.3 Privacy

Removed in Version 2.0. See Appendix B.

### 5.4 Usability and Accessibility

| ID | Requirement |
|---|---|
| NFR-4.1 | All interactive elements shall have screen reader labels. |
| NFR-4.2 | All pages shall remain usable at 200 percent browser zoom. |
| NFR-4.3 | The portal shall never use color as the only means of conveying information. |
| NFR-4.4 | Text and interface elements shall meet WCAG 2.2 AA contrast ratios. |
| NFR-4.5 | A first time user with a profile set shall be able to enhance an image within 3 clicks of the home page. |
| NFR-4.6 | The portal shall achieve a System Usability Scale score of 70 or higher in user testing. |

### 5.5 Reliability and Availability

| ID | Requirement |
|---|---|
| NFR-5.2 | The portal shall recover from AI or network failures without losing the current results. |
| NFR-5.3 | At least 99 percent of sessions during beta testing shall complete without a server error. |
| NFR-5.4 | The portal shall target 99 percent availability on the LAN host during the evaluation period. |

### 5.6 Accuracy

The targets in NFR-6.2 and NFR-6.3 are provisional until the enhancement and AI mapping approaches have been evaluated.

| ID | Requirement |
|---|---|
| NFR-6.1 | The Python simulation output shall match an independent reference implementation, such as the DaltonLens package, with a mean per pixel difference under 1 percent. |
| NFR-6.2 | Targeted enhancement shall reduce confusable pairs by at least 80 percent on the flat graphics test dataset. |
| NFR-6.3 | AI legend mapping shall be at least 90 percent correct on the labeled chart test set. |

### 5.7 Maintainability and Portability

| ID | Requirement |
|---|---|
| NFR-7.1 | The color engine shall be a separate Python package with unit tests covering at least 70 percent of its code. |
| NFR-7.2 | The codebase shall follow the architecture documented in Appendix C and consistent style rules. |
| NFR-7.3 | Every pull request shall pass automated builds and tests before merging. |
| NFR-7.4 | The color engine shall not depend on the web framework, to allow future reuse in other products. |

### 5.8 Deployment and Network

| ID | Requirement |
|---|---|
| NFR-8.1 | The portal shall listen on port 9090 on all host interfaces and be reachable at `http://<host-ip>:9090` from another device on the same LAN. |

## 6. Use Cases

### 6.1 UC-1: Enhance an Image

| Field | Description |
|---|---|
| Actor | User with CVD |
| Precondition | The user has opened the portal from a device on the LAN |
| Main flow | 1. User uploads an image.<br>2. System starts the pipeline and detects confusable pairs.<br>3. System displays the enhanced image with a before and after slider.<br>4. User downloads the result. |
| Alternate flow | No profile set: system asks the user to select one, then starts the pipeline. No confusable pairs found: system informs the user that no enhancement is needed. |
| Postcondition | Enhanced image is displayed and optionally downloaded |

### 6.2 UC-2: Interpret a Chart

| Field | Description |
|---|---|
| Actor | User with CVD |
| Precondition | An image is loaded and the server can reach the AI provider |
| Main flow | 1. User clicks Explain.<br>2. System returns a summary and legend mapping with verified or unverified flags.<br>3. User types a follow up question and receives an answer. |
| Alternate flow | AI unavailable: system shows an error and keeps other features working. Failed validation: items are marked unverified. Usage limit reached: system explains that AI is temporarily unavailable. |
| Postcondition | Interpretation is displayed and cached |

### 6.3 UC-3: Identify a Color

| Field | Description |
|---|---|
| Actor | Any user |
| Precondition | An image is open |
| Main flow | 1. User clicks or taps a point.<br>2. System displays the color name, values, and appearance under the active profile.<br>3. The result is announced to screen readers. |
| Postcondition | Color information is shown |

### 6.4 UC-4: Take the Calibration Test

Deferred. See Appendix B.

### 6.5 UC-5: Use Live Camera Mode

Deferred. See Appendix B.

### 6.6 UC-6: Simulate CVD for Content Review

| Field | Description |
|---|---|
| Actor | Designer or educator |
| Precondition | An image is loaded |
| Main flow | 1. User opens the simulator.<br>2. User selects a CVD type and severity.<br>3. System displays the simulated view and confusable pairs. |
| Postcondition | User understands how the content appears to CVD users |

## 7. Data Requirements

| Entity | Key Fields | Storage |
|---|---|---|
| CVDProfile | `cvd_type`, `severity`, `updated_at` | Browser storage |
| TemporaryImage | `id`, `original_path`, `working_path`, `image_hash`, `created_at`, `expires_at` | Server, temporary |
| Interpretation | `id`, `image_hash`, `summary`, `legend_mapping`, `verification_flags`, `created_at` | Server cache |
| AIUsage | `period`, `session_key`, `request_count`, `estimated_cost` | Server |
| NamedColor | `name`, `hex`, `lab_l`, `lab_a`, `lab_b`, `family` | Bundled with server |

Data retention: uploaded images and working copies expire after 24 hours by default. Cached interpretations expire after 30 days.

## 8. Acceptance Criteria and Verification

| Area | Verification Method | Acceptance Criteria |
|---|---|---|
| Color engine | Unit tests against an independent reference implementation | NFR-6.1 met |
| Enhancement | Before and after confusable pair count on the flat graphics test dataset | NFR-6.2 met |
| AI interpreter | Comparison with labeled chart ground truth | NFR-6.3 met |
| Performance | Server timing tests in the reference container and browser performance profiling | NFR-1.1, NFR-1.2, NFR-1.4, and NFR-1.5 met |
| Accessibility | axe automated checks and a screen reader walkthrough | NFR-4.1 to NFR-4.4 met |
| Usability | Task based user study with SUS survey | NFR-4.5 and NFR-4.6 met |
| Baseline | Task accuracy compared with the original image and a global daltonization filter | ChromaSense achieves higher accuracy |
| Network | Upload an image from a second device on the LAN, including a phone | NFR-8.1 met |
| Functional | pytest and Playwright suites in CI | All High priority FRs pass |

## 9. Requirements Traceability Matrix

| Feature | Functional Requirements | Related NFRs | Use Case |
|---|---|---|---|
| F1 Image input | FR-1.1 to FR-1.7 | NFR-1.1, NFR-2.3, NFR-8.1 | UC-1 |
| F2, F12 Profiles | FR-2.1 to FR-2.3 | NFR-4.1 | UC-1, UC-6 |
| F3 Simulation | FR-3.1 to FR-3.6 | NFR-1.1, NFR-6.1 | UC-6 |
| F4 Confusion detection | FR-4.1 to FR-4.6 | NFR-1.2 | UC-1, UC-6 |
| F5 Enhancement | FR-5.1 to FR-5.5 | NFR-1.1, NFR-6.2 | UC-1 |
| F10 Overlays | FR-6.3, FR-6.5 | NFR-4.3 | UC-1 |
| F6 Color identification | FR-7.1, FR-7.3 to FR-7.6 | NFR-4.1 | UC-3 |
| F7 Export | FR-8.1, FR-8.3 | NFR-1.1 | UC-1 |
| F8, F9 AI interpreter | FR-9.4 to FR-9.7, FR-9.9 | NFR-1.4, NFR-2.1, NFR-2.2, NFR-2.4, NFR-6.3 | UC-2 |
| Access without accounts | FR-12.2 | NFR-2.4, NFR-8.1 | All |

## Appendix A: Out of Scope Items

- Native mobile applications
- Browser extension
- Live camera mode and other video processing
- Personal calibration test
- User accounts and profile sync across devices
- Access from outside the LAN
- Medical diagnosis of CVD

## Appendix B: Deferred and Removed Requirements

Deferred items may return in a later release. Removed items no longer apply to the web portal or were removed by a team decision. The full Version 1.0 text is in `archive/BlindSpot_ChromaSense_SRS_v1.0.md`.

| ID | Version 1.0 requirement | Status | Reason |
|---|---|---|---|
| FR-2.4 | Set a default enhancement method and overlay style | Removed | Only one enhancement method remains |
| FR-2.5 | Sync profiles to the backend for signed in users | Deferred | No accounts in this release |
| FR-2.6 | Function fully offline without an account | Removed | Processing runs on the server |
| FR-6.1 | Segment natural images with a Core ML model | Deferred | High effort for a secondary feature |
| FR-6.2 | Segment charts with color clustering and connected components | Deferred | Overlays use the confusion mask instead |
| FR-6.4 | Place legend labels directly on chart regions | Deferred | Depends on locating chart regions reliably |
| FR-7.2 | Identify the average color of a brushed region | Deferred | Reduced scope |
| FR-8.2 | Share through the iOS share sheet | Deferred | Download covers the need in this release |
| FR-9.1 | Classify the image type on device | Deferred | Reduced scope |
| FR-9.2 | Extract legend and axis text with on device recognition | Deferred | The AI service reads text in this release |
| FR-9.3 | Request confirmation before sending an image to the AI service | Removed | Privacy requirements removed; AI runs only when the user clicks Explain |
| FR-9.8 | Read AI explanations aloud | Deferred | Reduced scope |
| FR-10.1 to FR-10.6 | Personal calibration test | Deferred | Evidence for severity estimation on uncalibrated displays is weak; users select a profile manually |
| FR-11.1 to FR-11.6 | Live camera mode | Deferred | Not realistic with server-side processing |
| FR-12.1 | Sign in with Apple | Deferred | No accounts in this release |
| FR-12.3 | Delete an account and server side data | Deferred | No accounts in this release |
| NFR-1.3 | Live camera at 30 frames per second | Deferred | Live camera deferred |
| NFR-2.5 | Session tokens in the iOS Keychain | Removed | No accounts or iOS client |
| NFR-3.1 | Process images entirely on device | Removed | Processing runs on the server; privacy requirements removed |
| NFR-3.2 | Images leave the device only after explicit user action | Removed | Privacy requirements removed |
| NFR-3.3 | Do not persist uploaded images on the backend | Removed | Privacy requirements removed; temporary storage is defined in Section 2.5 |
| NFR-3.4 | Request permissions only on first use | Removed | Privacy requirements removed |
| NFR-3.5 | Provide a privacy notice | Removed | Privacy requirements removed |
| NFR-5.1 | On device features remain available without network access | Removed | Processing runs on the server |
| UC-4 | Take the calibration test | Deferred | FR-10 deferred |
| UC-5 | Use live camera mode | Deferred | FR-11 deferred |

## Appendix C: Architecture Decisions

### Decision 1: Clean Architecture and Pipe and Filter

The system shall use Clean Architecture (Robert C. Martin) for the overall structure and Pipe and Filter for the processing pipeline. Source dependencies point inward, so the color rules and use cases do not depend on the web framework, storage, or AI provider. A use case runs the pipeline as a one-way sequence of independent filters: decode, downscale, confusion detection, and enhancement. AI interpretation is a separate use case and is not a pipeline filter.

This decision supports FR-1.7, NFR-7.1, NFR-7.2, and NFR-7.4. The design rules are in `dev/clean-architecture.mini.md`, and the full decision record is in `dev/architecture.md`.
