# Software Requirements Specification

**ChromaSense: AI Powered Color Accessibility Assistant for iOS**

Version 1.0

**Team BlindSpot**

- Sapnil Basnet
- Shivendra Bhagat
- Corbin Copper

Software Engineering Project  
Department of Computer Science, Texas State University  
September 2026

## Revision History

| Version | Date | Description | Authors |
|---|---|---|---|
| 1.0 | September 2026 | Initial SRS submission | Team BlindSpot |

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
  - [4.6 Pattern Overlays and Labels (F10)](#46-pattern-overlays-and-labels-f10)
  - [4.7 Color Identification (F6)](#47-color-identification-f6)
  - [4.8 Export and Sharing (F7)](#48-export-and-sharing-f7)
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

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the functional and non functional requirements for ChromaSense, a native iOS application developed by Team BlindSpot. The document serves as the agreed reference for design, implementation, testing, and evaluation, and is intended for the development team, the course instructor, and any testers or stakeholders.

### 1.2 Scope

ChromaSense helps people with color vision deficiency (CVD) understand color coded information in images and in the real world. Unlike global color filters, the system detects which colors are confusable for a specific user, enhances only those regions, and uses AI to explain the meaning of color coded content such as charts, maps, and legends. The application also includes a CVD simulator for people with normal color vision, a personal calibration test, and a live camera mode.

The system consists of an iOS client that performs color processing on device and a lightweight backend that handles AI interpretation, authentication, and profile synchronization. Android, web, and browser extension versions are outside the scope of this release.

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
| TestFlight | Apple service for distributing beta builds of iOS apps |

### 1.4 References

- IEEE Std 830-1998 and ISO/IEC/IEEE 29148:2018, Recommended practice and standard for software requirements specifications.
- Machado, G. M., Oliveira, M. M., and Fernandes, L. A. F. (2009). A Physiologically based Model for Simulation of Color Vision Deficiency. IEEE Transactions on Visualization and Computer Graphics.
- Brettel, H., Viénot, F., and Mollon, J. D. (1997). Computerized simulation of color appearance for dichromats. Journal of the Optical Society of America A.
- Sharma, G., Wu, W., and Dalal, E. N. (2005). The CIEDE2000 color difference formula: Implementation notes. Color Research and Application.
- Apple Inc. Human Interface Guidelines: Accessibility.
- W3C. Web Content Accessibility Guidelines (WCAG) 2.2.
- Team BlindSpot. ChromaSense Project Description, Version 3.0.

### 1.5 Document Overview

Section 2 describes the product context, users, environment, and constraints. Section 3 lists external interface requirements. Section 4 specifies functional requirements by feature. Section 5 specifies non functional requirements. Section 6 presents use cases. Section 7 defines the data requirements. Section 8 lists acceptance criteria and verification methods, and Section 9 contains the traceability matrix.

## 2. Overall Description

### 2.1 Product Perspective

ChromaSense is a new, self contained product. It replaces the general purpose approach of built in iOS color filters with content aware assistance. The major subsystems are listed below.

| Subsystem | Location | Responsibility |
|---|---|---|
| iOS client (SwiftUI) | Device | User interface, image input, simulator, overlays, color picker, calibration test, camera screen |
| Color engine | Device (Metal, Accelerate) | CVD simulation, confusion detection, targeted enhancement, color naming |
| Segmentation module | Device (Core ML) | Divides images into regions for per region overlays |
| Camera pipeline | Device (AVFoundation) | Captures frames and streams them to the color engine |
| Local store | Device (SwiftData) | Profiles, calibration results, recent images |
| Backend API | Server (FastAPI) | Authentication, rate limiting, AI request forwarding, profile sync |
| AI interpretation service | Server | Chart and map interpretation, visual Q&A, output validation |
| Database | Server (PostgreSQL) | User accounts, synced profiles, cached interpretations |

### 2.2 Product Functions

- Import images from Photos, Files, or the clipboard.
- Select or calibrate a CVD profile with type and severity.
- Simulate how an image appears to each CVD type.
- Detect confusable color pairs for the active profile.
- Enhance only confusable regions using selectable methods.
- Add pattern overlays and direct labels to confusable regions.
- Identify the name and values of a tapped color or region.
- Interpret charts and maps with AI and answer user questions.
- Apply simulation, enhancement, and color identification to the live camera feed.
- Save and share enhanced images, and sync profiles across devices.

### 2.3 User Classes and Characteristics

| User Class | Characteristics | Primary Features |
|---|---|---|
| Users with CVD | Varying CVD type and severity, general smartphone skills | Enhancement, overlays, color identification, AI interpreter, camera mode |
| Students and professionals with CVD | Frequently read charts, maps, and dashboards | AI interpreter, visual Q&A, overlays |
| Designers, educators, developers | Typical color vision, want to test content | Simulator, confusion detection |
| General public | Curious about CVD | Simulator, calibration test |

### 2.4 Operating Environment

- iPhone running iOS 17 or later.
- Live camera mode targets iPhone 12 or newer for real time performance.
- Network connection required only for AI interpretation, sign in, and profile sync.
- Backend hosted on a cloud platform supporting Python 3.11 or later and PostgreSQL.

### 2.5 Design and Implementation Constraints

- Client must be written in Swift using SwiftUI, Metal, and Apple frameworks.
- Development requires macOS with Xcode. Camera features require a physical iPhone for testing.
- LLM API keys must be stored on the backend and never embedded in the app.
- On device ML models must be converted to Core ML format and remain small enough for mobile use.
- The calibration test must use procedurally generated plates. Copyrighted test plates must not be used.
- The project must be completed within the course semester by a team of three.

### 2.6 User Documentation

- In app onboarding that explains CVD profiles, enhancement, and privacy.
- Contextual help screens for the calibration test and camera mode.
- README and setup guide in the project repository.

### 2.7 Assumptions and Dependencies

- A third party vision language model API remains available at an acceptable cost.
- Users grant photo library and camera permissions when prompted.
- Display color accuracy depends on device settings such as brightness, True Tone, and Night Shift.
- Published CVD simulation models are sufficiently accurate for the purposes of this application.
- The team has access to an Apple Developer account for TestFlight distribution.

## 3. External Interface Requirements

### 3.1 User Interfaces

- Home screen with options to import an image, open the camera, open the simulator, and take the calibration test.
- Image workspace with a before and after swipe slider, a toolbar for enhancement method, overlay style, and AI interpretation, and a tap or brush color picker.
- Simulator screen with CVD type selector and severity slider.
- Camera screen with live preview, mode selector, center reticle, and freeze frame button.
- AI panel showing the interpretation summary, legend mapping, confidence indicators, and a text or voice question field.
- Settings screen for profile, enhancement defaults, account, and privacy options.
- All screens follow Apple Human Interface Guidelines and must never rely on color alone to convey information.

### 3.2 Hardware Interfaces

- Rear camera through AVFoundation for live camera mode.
- GPU through Metal for simulation and enhancement.
- Neural Engine through Core ML for segmentation and classification.
- Microphone for voice questions, used only when the user activates voice input.

### 3.3 Software Interfaces

| Interface | Purpose |
|---|---|
| PhotosUI and Photos | Import images and save enhanced results |
| Vision framework | Text recognition for legends and axis labels, image classification |
| Speech and AVSpeechSynthesizer | Voice questions and spoken explanations |
| Sign in with Apple | User authentication |
| SwiftData | Local persistence |
| Vision language model API | Chart and map interpretation, accessed only through the backend |
| PostgreSQL | Server side persistence |

### 3.4 Communication Interfaces

- All client and server communication uses HTTPS with TLS 1.2 or later.
- The backend exposes a REST API with JSON payloads.
- Authenticated requests carry a session token issued after Sign in with Apple verification.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/apple` | Verify Sign in with Apple token and return a session |
| GET, PUT | `/api/profile` | Read or update the CVD profile |
| POST | `/api/calibration` | Store calibration test results |
| POST | `/api/interpret` | Return AI chart or map interpretation |
| POST | `/api/ask` | Answer a question about an interpreted image |

## 4. Functional Requirements

Priority levels: High requirements form the MVP, Medium requirements are core differentiators, and Low requirements are enhancements that may be deferred. Live camera mode is a committed stretch goal.

### 4.1 Image Input (F1)

| ID | Requirement | Priority |
|---|---|---|
| FR-1.1 | The system shall allow the user to select an image from the Photos library. | High |
| FR-1.2 | The system shall allow the user to import an image from the Files app. | High |
| FR-1.3 | The system shall allow the user to paste an image from the clipboard. | Medium |
| FR-1.4 | The system shall accept PNG, JPEG, HEIC, and WEBP images. | High |
| FR-1.5 | The system shall downscale images larger than 12 megapixels for analysis while preserving the original for export. | High |
| FR-1.6 | The system shall display an error message for unsupported or corrupted files. | High |

### 4.2 CVD Profile Management (F2, F12)

| ID | Requirement | Priority |
|---|---|---|
| FR-2.1 | The system shall allow the user to select a CVD type: protan, deutan, tritan, or achromatopsia. | High |
| FR-2.2 | The system shall allow the user to set severity from 0 to 1 using a slider. | High |
| FR-2.3 | The system shall store the active profile locally and apply it to all features. | High |
| FR-2.4 | The system shall allow the user to set a default enhancement method and overlay style. | Medium |
| FR-2.5 | The system shall sync profiles to the backend for signed in users. | Medium |
| FR-2.6 | The system shall function fully offline without an account, except for AI and sync features. | High |

### 4.3 CVD Simulation (F3)

| ID | Requirement | Priority |
|---|---|---|
| FR-3.1 | The system shall simulate protan and deutan deficiencies using the Machado (2009) model with variable severity. | High |
| FR-3.2 | The system shall simulate tritan deficiency using the Brettel (1997) model. | High |
| FR-3.3 | The system shall simulate achromatopsia using luminance based conversion. | High |
| FR-3.4 | The system shall perform simulation in linear RGB space. | High |
| FR-3.5 | The system shall display original and simulated images side by side or with a swipe slider. | High |
| FR-3.6 | The system shall update the simulated view in real time as severity changes. | Medium |

### 4.4 Confusion Detection (F4)

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
| FR-5.2 | The system shall support targeted daltonization, lightness separation, and hue rotation methods. | High |
| FR-5.3 | The system shall verify enhancement by re-running confusion detection on the result. | High |
| FR-5.4 | The system shall allow the user to adjust enhancement strength. | Medium |
| FR-5.5 | The system shall allow the user to toggle between original and enhanced views. | High |

### 4.6 Pattern Overlays and Labels (F10)

| ID | Requirement | Priority |
|---|---|---|
| FR-6.1 | The system shall segment images into regions using a Core ML segmentation model for natural images. | Medium |
| FR-6.2 | The system shall segment charts using color clustering and connected component analysis. | Medium |
| FR-6.3 | The system shall apply a distinct pattern (hatching, dots, crosshatch, or outline) to each confusable color group. | Medium |
| FR-6.4 | The system shall place legend labels directly on chart regions when a legend mapping is available. | Medium |
| FR-6.5 | The system shall allow the user to toggle overlays on and off. | Medium |

### 4.7 Color Identification (F6)

| ID | Requirement | Priority |
|---|---|---|
| FR-7.1 | The system shall identify the color of a tapped point. | High |
| FR-7.2 | The system shall identify the average color of a brushed region. | Medium |
| FR-7.3 | The system shall return the nearest color name using CIEDE2000 against a bundled named color dataset. | High |
| FR-7.4 | The system shall display HEX, RGB, and HSL values and the basic color family. | High |
| FR-7.5 | The system shall show how the identified color appears under the active profile. | Medium |
| FR-7.6 | The system shall announce identification results through VoiceOver. | High |

### 4.8 Export and Sharing (F7)

| ID | Requirement | Priority |
|---|---|---|
| FR-8.1 | The system shall save the enhanced image to the Photos library. | High |
| FR-8.2 | The system shall share the enhanced image through the iOS share sheet. | High |
| FR-8.3 | The system shall export at the original image resolution. | Medium |

### 4.9 AI Chart and Map Interpreter (F8, F9)

| ID | Requirement | Priority |
|---|---|---|
| FR-9.1 | The system shall classify an image as chart, map, photo, screenshot, or other on device. | Medium |
| FR-9.2 | The system shall extract text from legends and axes using on device text recognition. | Medium |
| FR-9.3 | The system shall request user confirmation before sending an image to the AI service. | High |
| FR-9.4 | The backend shall request structured output containing chart type, legend entries, color mapping, and a summary. | Medium |
| FR-9.5 | The system shall validate AI legend colors against colors detected on device and flag mismatches. | Medium |
| FR-9.6 | The system shall display a confidence indicator for each interpreted item. | Medium |
| FR-9.7 | The system shall allow follow up questions by text or voice, grounded in the same image context. | Medium |
| FR-9.8 | The system shall read AI explanations aloud on request. | Medium |
| FR-9.9 | The system shall show a clear message when the AI service is unavailable. | High |

### 4.10 Personal Calibration Test (F11)

| ID | Requirement | Priority |
|---|---|---|
| FR-10.1 | The system shall generate pseudoisochromatic plates procedurally along known confusion lines. | Medium |
| FR-10.2 | The system shall include a drag to reorder hue arrangement task. | Medium |
| FR-10.3 | The system shall estimate CVD type and severity from test results. | Medium |
| FR-10.4 | The system shall instruct users to set full brightness and disable True Tone and Night Shift before testing. | Medium |
| FR-10.5 | The system shall display a disclaimer that the test is not a medical diagnosis. | High |
| FR-10.6 | The system shall allow the user to apply the estimated result as the active profile. | Medium |

### 4.11 Live Camera Mode (F14)

| ID | Requirement | Priority |
|---|---|---|
| FR-11.1 | The system shall display a live camera preview with simulation or enhancement applied. | Medium |
| FR-11.2 | The system shall continuously identify the color under a center reticle. | Medium |
| FR-11.3 | The system shall allow the user to switch between original, simulated, and enhanced modes. | Medium |
| FR-11.4 | The system shall allow the user to freeze a frame and open it in the image workspace or AI interpreter. | Medium |
| FR-11.5 | The system shall allow the user to lock exposure and white balance. | Low |
| FR-11.6 | The system shall process camera frames entirely on device. | High |

### 4.12 Accounts and Authentication

| ID | Requirement | Priority |
|---|---|---|
| FR-12.1 | The system shall support Sign in with Apple. | Medium |
| FR-12.2 | The system shall allow use without an account for all on device features. | High |
| FR-12.3 | The system shall allow users to delete their account and all server side data. | Medium |

## 5. Non Functional Requirements

### 5.1 Performance

| ID | Requirement |
|---|---|
| NFR-1.1 | Simulation and enhancement of a 12 megapixel image shall complete in under 1 second on iPhone 12 or newer. |
| NFR-1.2 | Confusion detection shall complete in under 500 milliseconds on a downscaled image. |
| NFR-1.3 | Live camera mode shall render at 30 frames per second or higher on iPhone 12 or newer. |
| NFR-1.4 | AI interpretation shall return a result within 8 seconds under normal network conditions. |
| NFR-1.5 | The app shall launch to an interactive home screen within 2 seconds. |

### 5.2 Security

| ID | Requirement |
|---|---|
| NFR-2.1 | All network traffic shall use HTTPS with TLS 1.2 or later. |
| NFR-2.2 | API keys for third party services shall reside only on the backend. |
| NFR-2.3 | The backend shall validate all inputs and limit image upload size to 10 MB. |
| NFR-2.4 | The backend shall rate limit AI requests per user. |
| NFR-2.5 | Session tokens shall expire and be stored in the iOS Keychain. |

### 5.3 Privacy

| ID | Requirement |
|---|---|
| NFR-3.1 | Simulation, enhancement, color identification, and camera processing shall run entirely on device. |
| NFR-3.2 | Images shall leave the device only after explicit user action to request AI interpretation. |
| NFR-3.3 | The backend shall not persist uploaded images. Only interpretation results and an image hash may be cached. |
| NFR-3.4 | Camera, photo, and microphone permissions shall be requested only when the related feature is first used. |
| NFR-3.5 | The app shall provide a privacy notice describing data collection and use. |

### 5.4 Usability and Accessibility

| ID | Requirement |
|---|---|
| NFR-4.1 | All interactive elements shall have VoiceOver labels. |
| NFR-4.2 | The app shall support Dynamic Type at all standard sizes. |
| NFR-4.3 | The app shall never use color as the only means of conveying information. |
| NFR-4.4 | Text and interface elements shall meet WCAG 2.2 AA contrast ratios. |
| NFR-4.5 | A first time user shall be able to enhance an image within 3 taps of the home screen. |
| NFR-4.6 | The app shall achieve a System Usability Scale score of 70 or higher in user testing. |

### 5.5 Reliability and Availability

| ID | Requirement |
|---|---|
| NFR-5.1 | On device features shall remain available without network access. |
| NFR-5.2 | The app shall recover from AI or network failures without crashing and preserve user work. |
| NFR-5.3 | The crash free session rate during beta testing shall be at least 99 percent. |
| NFR-5.4 | The backend shall target 99 percent availability during the evaluation period. |

### 5.6 Accuracy

| ID | Requirement |
|---|---|
| NFR-6.1 | The Metal simulation output shall match the Python reference implementation with a mean per pixel difference under 1 percent. |
| NFR-6.2 | Targeted enhancement shall reduce confusable pairs by at least 80 percent on the test dataset. |
| NFR-6.3 | AI legend mapping shall be at least 90 percent correct on the labeled chart test set. |

### 5.7 Maintainability and Portability

| ID | Requirement |
|---|---|
| NFR-7.1 | The color engine shall be a separate Swift module with unit tests covering at least 70 percent of its code. |
| NFR-7.2 | The codebase shall follow a documented architecture (MVVM on the client) and consistent style rules. |
| NFR-7.3 | Every pull request shall pass automated builds and tests before merging. |
| NFR-7.4 | The color engine design shall allow future reuse in a browser extension or Android version. |

## 6. Use Cases

### 6.1 UC-1: Enhance an Image

| Field | Description |
|---|---|
| Actor | User with CVD |
| Precondition | A CVD profile is set |
| Main flow | 1. User imports an image.<br>2. System detects confusable pairs.<br>3. System displays the enhanced image with a before and after slider.<br>4. User saves or shares the result. |
| Alternate flow | No confusable pairs found: system informs the user that no enhancement is needed. |
| Postcondition | Enhanced image is displayed and optionally saved |

### 6.2 UC-2: Interpret a Chart

| Field | Description |
|---|---|
| Actor | User with CVD |
| Precondition | An image is loaded and network is available |
| Main flow | 1. User taps Explain.<br>2. System asks for confirmation to send the image.<br>3. User confirms.<br>4. System returns a summary, legend mapping, and labeled overlays.<br>5. User asks a follow up question and receives an answer. |
| Alternate flow | AI unavailable: system shows an error and keeps on device features working. Low confidence: items are marked uncertain. |
| Postcondition | Interpretation is displayed and cached |

### 6.3 UC-3: Identify a Color

| Field | Description |
|---|---|
| Actor | Any user |
| Precondition | An image or camera view is open |
| Main flow | 1. User taps a point or brushes a region.<br>2. System displays the color name, values, and appearance under the active profile.<br>3. VoiceOver announces the result. |
| Postcondition | Color information is shown |

### 6.4 UC-4: Take the Calibration Test

| Field | Description |
|---|---|
| Actor | Any user |
| Precondition | None |
| Main flow | 1. System shows display setting instructions and a disclaimer.<br>2. User completes plates and the hue task.<br>3. System estimates type and severity.<br>4. User applies the result as the active profile. |
| Alternate flow | User exits early: no profile change is made. |
| Postcondition | Calibration result is stored |

### 6.5 UC-5: Use Live Camera Mode

| Field | Description |
|---|---|
| Actor | User with CVD |
| Precondition | Camera permission granted |
| Main flow | 1. User opens the camera.<br>2. System shows the enhanced live feed and names the color under the reticle.<br>3. User freezes a frame.<br>4. User opens the frame in the AI interpreter. |
| Alternate flow | Permission denied: system explains why access is needed and links to Settings. |
| Postcondition | Frame is optionally saved or interpreted |

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
| User | `id`, `apple_user_id`, `created_at` | Server |
| CVDProfile | `id`, `user_id`, `cvd_type`, `severity`, `enhancement_style`, `updated_at` | Device and server |
| CalibrationResult | `id`, `user_id`, `plate_scores`, `hue_task_score`, `estimated_type`, `estimated_severity`, `created_at` | Device and server |
| SavedImage | `id`, `original_asset_id`, `processed_path`, `image_type`, `created_at` | Device only |
| Interpretation | `id`, `image_hash`, `summary`, `legend_mapping`, `confidence`, `created_at` | Device and server cache |
| NamedColor | `name`, `hex`, `lab_l`, `lab_a`, `lab_b`, `family` | Bundled with app |

Data retention: cached interpretations expire after 30 days. Account deletion removes all server side records for that user.

## 8. Acceptance Criteria and Verification

| Area | Verification Method | Acceptance Criteria |
|---|---|---|
| Color engine | Unit tests against Python reference | NFR-6.1 met |
| Enhancement | Before and after confusable pair count on test dataset | NFR-6.2 met |
| AI interpreter | Comparison with labeled chart ground truth | NFR-6.3 met |
| Performance | Instruments profiling on iPhone 12 or newer | NFR-1.1 to NFR-1.5 met |
| Accessibility | Xcode Accessibility Inspector and VoiceOver walkthrough | NFR-4.1 to NFR-4.4 met |
| Usability | Task based user study with SUS survey | NFR-4.5 and NFR-4.6 met |
| Baseline | Task accuracy compared with built in iOS color filters | ChromaSense achieves higher accuracy |
| Functional | XCTest, XCUITest, and Pytest suites in CI | All High priority FRs pass |

## 9. Requirements Traceability Matrix

| Feature | Functional Requirements | Related NFRs | Use Case |
|---|---|---|---|
| F1 Image input | FR-1.1 to FR-1.6 | NFR-1.1, NFR-2.3 | UC-1 |
| F2, F12 Profiles | FR-2.1 to FR-2.6 | NFR-5.1 | UC-1, UC-4 |
| F3 Simulation | FR-3.1 to FR-3.6 | NFR-1.1, NFR-6.1 | UC-6 |
| F4 Confusion detection | FR-4.1 to FR-4.6 | NFR-1.2 | UC-1, UC-6 |
| F5 Enhancement | FR-5.1 to FR-5.5 | NFR-1.1, NFR-6.2 | UC-1 |
| F10 Overlays | FR-6.1 to FR-6.5 | NFR-4.3 | UC-1, UC-2 |
| F6 Color identification | FR-7.1 to FR-7.6 | NFR-4.1 | UC-3 |
| F7 Export | FR-8.1 to FR-8.3 | NFR-3.4 | UC-1 |
| F8, F9 AI interpreter | FR-9.1 to FR-9.9 | NFR-1.4, NFR-3.2, NFR-6.3 | UC-2 |
| F11 Calibration | FR-10.1 to FR-10.6 | NFR-4.5 | UC-4 |
| F14 Live camera | FR-11.1 to FR-11.6 | NFR-1.3, NFR-3.1 | UC-5 |
| Accounts | FR-12.1 to FR-12.3 | NFR-2.1, NFR-2.5 | All |

## Appendix A: Out of Scope Items

- Android application
- Web application and browser extension
- Video processing
- Medical diagnosis of CVD
- App Store public release during the course
