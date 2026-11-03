"use strict";
window.ChromaSense = window.ChromaSense || {};

(function setUpSpeech() {
  const RATE_KEY = "chromasense.speechRate";
  const AUTO_KEY = "chromasense.speechAuto";
  const textSources = new Map();
  let activeStatus = null;

  const available = () => "speechSynthesis" in window;

  function rate() {
    const stored = Number(localStorage.getItem(RATE_KEY));
    return stored >= 0.5 && stored <= 2 ? stored : 1;
  }

  const automaticReading = () => localStorage.getItem(AUTO_KEY) === "true";

  function setStatus(statusElement, text) {
    if (statusElement) {
      statusElement.textContent = text;
    }
    ChromaSense.announce(text);
  }

  function speak(text, statusElement, label) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = rate();
    utterance.onend = () => {
      if (statusElement) {
        statusElement.textContent = `Finished reading the ${label}.`;
      }
    };
    activeStatus = statusElement;
    window.speechSynthesis.speak(utterance);
  }

  function textFor(targetId) {
    if (textSources.has(targetId)) {
      return textSources.get(targetId)();
    }
    const target = document.getElementById(targetId);
    return target ? target.innerText : "";
  }

  function buildControls(holder) {
    const label = holder.dataset.speechLabel;
    if (!available()) {
      holder.replaceChildren(
        ChromaSense.workspace.element("p", "", `This browser cannot read the ${label} aloud.`),
      );
      return;
    }
    const { element } = ChromaSense.workspace;
    const startButton = element("button", "", `Read the ${label} aloud`);
    const pauseButton = element("button", "", `Pause reading the ${label}`);
    const stopButton = element("button", "", `Stop reading the ${label}`);
    const status = element("p", "", "Not reading.");
    [startButton, pauseButton, stopButton].forEach((button) => {
      button.type = "button";
    });
    let paused = false;

    const resetPause = () => {
      paused = false;
      pauseButton.textContent = `Pause reading the ${label}`;
    };

    startButton.addEventListener("click", () => {
      const text = textFor(holder.dataset.speechTarget);
      if (!text.trim()) {
        setStatus(status, `There is no ${label} to read yet.`);
        return;
      }
      resetPause();
      speak(text, status, label);
      setStatus(status, `Reading the ${label}.`);
    });

    pauseButton.addEventListener("click", () => {
      if (paused) {
        window.speechSynthesis.resume();
        resetPause();
        setStatus(status, `Reading the ${label}.`);
      } else {
        window.speechSynthesis.pause();
        paused = true;
        pauseButton.textContent = `Resume reading the ${label}`;
        setStatus(status, `Paused reading the ${label}.`);
      }
    });

    stopButton.addEventListener("click", () => {
      window.speechSynthesis.cancel();
      resetPause();
      setStatus(status, `Stopped reading the ${label}.`);
    });

    holder.replaceChildren(startButton, pauseButton, stopButton, status);
  }

  function startControls(root) {
    root.querySelectorAll(".speech-controls").forEach(buildControls);
  }

  /** Read a new result only when the user turned on automatic reading. */
  function newResult(text) {
    if (available() && automaticReading() && text && text.trim()) {
      speak(text, activeStatus, "result");
    }
  }

  function startSettings() {
    const rateInput = document.getElementById("speech-rate");
    if (!rateInput) {
      return;
    }
    const output = document.getElementById("speech-rate-value");
    const auto = document.getElementById("speech-auto");
    document.getElementById("speech-settings-unavailable").hidden = available();
    rateInput.value = String(rate());
    output.textContent = rateInput.value;
    auto.checked = automaticReading();
    rateInput.addEventListener("input", () => {
      localStorage.setItem(RATE_KEY, rateInput.value);
      output.textContent = rateInput.value;
    });
    rateInput.addEventListener("change", () =>
      ChromaSense.announce(`Speech rate saved: ${rateInput.value}.`),
    );
    auto.addEventListener("change", () => {
      localStorage.setItem(AUTO_KEY, String(auto.checked));
      ChromaSense.announce(`Automatic reading is ${auto.checked ? "on" : "off"}.`);
    });
  }

  ChromaSense.speech = {
    newResult,
    registerText: (id, source) => textSources.set(id, source),
    startControls,
  };
  document.addEventListener("DOMContentLoaded", startSettings);
})();
