"use strict";
window.ChromaSense = window.ChromaSense || {};

(function setUpSimulator() {
  const PREVIEW_DELAY_MS = 250;
  const NAMES = {
    protan: "protan",
    deutan: "deutan",
    tritan: "tritan",
    achromatopsia: "achromatopsia",
  };

  async function start() {
    const holder = document.getElementById("simulator");
    if (!holder) {
      return;
    }
    const imageId = holder.dataset.imageId;
    const typeSelect = document.getElementById("simulator-type");
    const severity = document.getElementById("simulator-severity");
    const saved = ChromaSense.profile.get();
    if (saved && saved.type !== "none") {
      typeSelect.value = saved.type;
      severity.value = String(saved.severity);
    }
    document.getElementById("simulator-severity-value").textContent = severity.value;

    const response = await fetch(`/api/images/${imageId}/analysis`);
    if (!response.ok) {
      const failure = document.getElementById("simulator-error");
      failure.textContent = await ChromaSense.errorMessage(response);
      failure.hidden = false;
      ChromaSense.announce(failure.textContent);
      return;
    }
    const { analysis } = await response.json();
    document.getElementById("simulator-summary").textContent = analysis.summary;
    const original = document.getElementById("simulator-original");
    original.src = `/api/images/${imageId}/render?view=original`;
    original.alt = `Original view. ${analysis.summary}`;

    const selection = () => ({ type: typeSelect.value, severity: Number(severity.value) });

    function updateView() {
      const current = selection();
      const query = new URLSearchParams({ view: "simulated" });
      ChromaSense.profile.addProfileTo(query, current);
      const simulated = document.getElementById("simulator-simulated");
      simulated.src = `/api/images/${imageId}/render?${query}`;
      const description =
        `Simulated view, ${NAMES[current.type]}, severity ${current.severity}.`;
      simulated.alt = `${description} ${analysis.summary}`;
      document.getElementById("simulator-caption").textContent = description;
      document.getElementById("achromatopsia-note").hidden = current.type !== "achromatopsia";
      return description;
    }

    async function updatePairs() {
      const result = await fetch(`/api/images/${imageId}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(ChromaSense.profile.profileBody(selection())),
      });
      if (result.ok) {
        const { pairs, groups } = await result.json();
        ChromaSense.workspace.fillPairs(
          "simulator-pair-list",
          "simulator-pair-empty",
          analysis,
          pairs,
          groups,
        );
      }
    }

    const refresh = ChromaSense.debounce(async () => {
      const description = updateView();
      await updatePairs();
      ChromaSense.announce(`Updated. ${description}`);
    }, PREVIEW_DELAY_MS);

    severity.addEventListener("input", () => {
      document.getElementById("simulator-severity-value").textContent = severity.value;
      refresh();
    });
    typeSelect.addEventListener("change", refresh);

    updateView();
    await updatePairs();
  }

  document.addEventListener("DOMContentLoaded", start);
})();
