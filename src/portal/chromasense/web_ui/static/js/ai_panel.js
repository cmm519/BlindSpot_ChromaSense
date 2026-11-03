"use strict";
window.ChromaSense = window.ChromaSense || {};

(function setUpAiPanel() {
  function setBusy(busy) {
    document.getElementById("ai-panel").setAttribute("aria-busy", String(busy));
  }

  function showMessage(text) {
    const message = document.getElementById("ai-message");
    message.textContent = text;
    message.hidden = !text;
  }

  function failureMessage(status, serverMessage) {
    if (status === 429) {
      return `You have made too many AI requests. ${serverMessage}`;
    }
    if (status === 503) {
      return `${serverMessage} Your other results are still here.`;
    }
    if (status === 409) {
      return "Click Explain first, and then ask your question.";
    }
    return serverMessage;
  }

  function renderAiColor(item) {
    const { element, flagged, swatch } = ChromaSense.workspace;
    const node = element("li");
    node.dataset.itemId = item.item_id;
    if (item.rgb) {
      node.append(swatch(item.rgb));
      node.append(`Color: ${item.name}. HEX ${item.hex}. Color family: ${item.family}.`);
    } else {
      node.append(`Color: the AI named palette color ${item.palette_id}, which this image does not have.`);
    }
    node.append(flagged(item));
    return node;
  }

  function spokenText() {
    const parts = [];
    const results = document.getElementById("ai-results");
    if (!results.hidden) {
      parts.push(results.innerText);
    }
    const answers = document.getElementById("answer-list");
    if (answers.children.length) {
      parts.push(answers.innerText);
    }
    return parts.join("\n");
  }

  function showInterpretation(state, result) {
    const { fillList, renderLegend, renderShape, renderText, colorsById } = ChromaSense.workspace;
    const colors = new Map([
      ...colorsById(state.analysis),
      ...result.color_items.map((item) => [item.palette_id, item]),
    ]);
    document.getElementById("ai-chart-type").textContent = result.chart_type;
    document.getElementById("ai-summary").textContent = result.summary;
    fillList("ai-legend", null, result.legend, (item) => renderLegend(item, colors));
    fillList("ai-text", null, result.text_items, renderText);
    fillList("ai-shapes", null, result.shape_items, renderShape);
    fillList("ai-colors", null, result.color_items, renderAiColor);
    document.getElementById("ai-results").hidden = false;

    // The local lists hold the same items, so they take the new flags too.
    const local = result.text_items.filter((item) => item.source !== "ai");
    const shapes = result.shape_items.filter((item) => item.source !== "ai");
    const legend = result.legend.filter((item) => item.source !== "ai");
    fillList("text-list", "text-empty", local, renderText);
    fillList("shape-list", "shape-empty", shapes, renderShape);
    fillList("legend-list", "legend-empty", legend, (item) => renderLegend(item, colors));

    state.interpretationSummary = result.summary;
    const summary = document.getElementById("interpretation-summary");
    summary.textContent = `AI summary: ${result.summary}`;
    summary.hidden = false;
    ChromaSense.workspace.updateAlternatives(state);
  }

  function showAnswer(result) {
    const { element } = ChromaSense.workspace;
    const item = element("li");
    item.append(`Answer: ${result.text} Flag: `);
    item.append(element("span", "flag", result.verification));
    item.append(". ");
    item.append(
      result.cited_item_ids.length
        ? `It cites: ${result.cited_item_ids.join(", ")}.`
        : "It cites no items.",
    );
    document.getElementById("answer-list").append(item);
    document.getElementById("answers-heading").hidden = false;
  }

  async function post(url, body) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  /** Run one AI request. Controls stay enabled, so that keyboard focus never moves. */
  function runner(busyState, startMessage) {
    return async function run(url, body, onSuccess) {
      if (busyState.busy) {
        return;
      }
      busyState.busy = true;
      setBusy(true);
      showMessage("");
      ChromaSense.announce(startMessage);
      try {
        const response = await post(url, body);
        if (response.ok) {
          await onSuccess(await response.json());
        } else {
          const text = failureMessage(response.status, await ChromaSense.errorMessage(response));
          showMessage(text);
          ChromaSense.announce(`The AI request failed. ${text}`);
        }
      } catch (error) {
        const text = "The AI request could not reach the server. Your other results are still here.";
        showMessage(text);
        ChromaSense.announce(`The AI request failed. ${text}`);
      } finally {
        busyState.busy = false;
        setBusy(false);
      }
    };
  }

  function start(state) {
    const busyState = { busy: false };
    const explain = runner(busyState, "Explain started. Asking the AI service.");
    const ask = runner(busyState, "Question sent to the AI service.");

    ChromaSense.speech.registerText("ai-panel-spoken", spokenText);

    document.getElementById("explain-button").addEventListener("click", () =>
      explain("/api/interpret", { image_id: state.imageId }, (result) => {
        showInterpretation(state, result);
        ChromaSense.announce("Explain finished. The AI results are in the AI interpretation section.");
        ChromaSense.speech.newResult(spokenText());
      }),
    );

    document.getElementById("question-form").addEventListener("submit", (event) => {
      event.preventDefault();
      const input = document.getElementById("question-input");
      const question = input.value.trim();
      if (!question) {
        showMessage("Type a question first.");
        ChromaSense.announce("Type a question first.");
        return;
      }
      ask("/api/ask", { image_id: state.imageId, question }, (result) => {
        showAnswer(result);
        input.value = "";
        ChromaSense.announce(`Answer received, flagged ${result.verification}. ${result.text}`);
        ChromaSense.speech.newResult(document.getElementById("answer-list").lastElementChild.innerText);
      });
    });
  }

  ChromaSense.aiPanel = { start };
})();
