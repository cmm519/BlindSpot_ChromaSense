"use strict";
window.ChromaSense = window.ChromaSense || {};

(function setUpWorkspace() {
  const SOURCE_NAMES = { local: "local analysis", ai: "AI", both: "AI and local analysis" };

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== undefined) {
      node.textContent = text;
    }
    return node;
  }

  /** A color sample for sighted users. Its name is always in the text beside it. */
  function swatch(rgb) {
    const node = element("span", "swatch");
    node.setAttribute("aria-hidden", "true");
    node.style.backgroundColor = `rgb(${rgb.join(", ")})`;
    return node;
  }

  function flagged(item) {
    const fragment = document.createDocumentFragment();
    fragment.append(` Source: ${SOURCE_NAMES[item.source]}. Flag: `);
    fragment.append(element("span", "flag", item.verification));
    fragment.append(".");
    return fragment;
  }

  function fillList(listId, emptyId, items, render) {
    const list = document.getElementById(listId);
    list.replaceChildren(...items.map(render));
    if (emptyId) {
      document.getElementById(emptyId).hidden = items.length > 0;
    }
  }

  function location(item) {
    return item.x === null || item.x === undefined
      ? ""
      : ` Location: ${item.x} pixels from the left, ${item.y} pixels from the top, ${item.width} by ${item.height} pixels.`;
  }

  function colorsById(analysis) {
    return new Map(analysis.color_items.map((item) => [item.palette_id, item]));
  }

  function colorName(colors, paletteId) {
    const color = colors.get(paletteId);
    return color ? color.name : `palette color ${paletteId}`;
  }

  function patternFor(groups, paletteId) {
    const group = groups.find((entry) => entry.palette_ids.includes(paletteId));
    return group ? group.pattern : "none";
  }

  function renderPair(pair, colors, groups) {
    const item = element("li");
    item.tabIndex = 0;
    const first = colors.get(pair.a_id);
    const second = colors.get(pair.b_id);
    if (first) {
      item.append(swatch(first.rgb));
    }
    if (second) {
      item.append(swatch(second.rgb));
    }
    item.append(
      `${colorName(colors, pair.a_id)} and ${colorName(colors, pair.b_id)} look alike. ` +
        `Original distance ${pair.original_distance.toFixed(1)}, ` +
        `simulated distance ${pair.simulated_distance.toFixed(1)}. ` +
        `Pattern: ${patternFor(groups, pair.a_id)}.`,
    );
    return item;
  }

  function fillPairs(listId, emptyId, analysis, pairs, groups) {
    const colors = colorsById(analysis);
    fillList(listId, emptyId, pairs, (pair) => renderPair(pair, colors, groups));
  }

  function renderColor(color, colors, pairs, groups) {
    const item = element("li");
    item.tabIndex = 0;
    const partners = pairs
      .filter((pair) => pair.a_id === color.palette_id || pair.b_id === color.palette_id)
      .map((pair) =>
        colorName(colors, pair.a_id === color.palette_id ? pair.b_id : pair.a_id),
      );
    item.append(swatch(color.rgb));
    item.append(
      `${color.name}. HEX ${color.hex}. RGB ${color.rgb.join(", ")}. ` +
        `HSL ${color.hsl[0]} degrees, ${color.hsl[1]} percent, ${color.hsl[2]} percent. ` +
        `Color family: ${color.family}. Pattern: ${patternFor(groups, color.palette_id)}. ` +
        `Confused with: ${partners.length ? partners.join(", ") : "no other color"}.`,
    );
    item.append(flagged(color));
    return item;
  }

  function renderText(item) {
    const node = element("li");
    node.dataset.itemId = item.item_id;
    node.append(`Text: ${item.text}.${location(item)}`);
    node.append(flagged(item));
    return node;
  }

  function renderShape(item) {
    const node = element("li");
    node.dataset.itemId = item.item_id;
    const name = item.color_name || "unknown color";
    node.append(`Shape: ${item.kind}, color ${name}.${location(item)}`);
    node.append(flagged(item));
    return node;
  }

  function renderLegend(item, colors) {
    const node = element("li");
    node.dataset.itemId = item.item_id;
    const name = item.palette_id === null ? "no color" : colorName(colors, item.palette_id);
    node.append(`Legend entry: ${item.text}, color ${name}.`);
    if (item.reason) {
      node.append(` ${item.reason}.`);
    }
    node.append(flagged(item));
    return node;
  }

  function renderRegion(region, colors) {
    return element(
      "li",
      "",
      `Region ${region.id}: ${colorName(colors, region.palette_id)}. ` +
        `${region.width} by ${region.height} pixels, ${region.area} pixels in area. ` +
        `Location: ${region.x} pixels from the left, ${region.y} pixels from the top. ` +
        `Center: ${Math.round(region.center_x)}, ${Math.round(region.center_y)}.`,
    );
  }

  function imageUrl(state, view, strength) {
    const query = new URLSearchParams({ view });
    if (view === "original") {
      query.append("cvd_type", "none");
    } else {
      ChromaSense.profile.addProfileTo(query, state.profile);
    }
    if (view === "enhanced" || view === "overlay") {
      query.append("strength", String(strength));
    }
    return `/api/images/${state.imageId}/render?${query}`;
  }

  function fillLocalResults(state) {
    const { analysis, pairs, groups } = state;
    const colors = colorsById(analysis);
    fillList("color-list", null, analysis.color_items, (color) =>
      renderColor(color, colors, pairs, groups),
    );
    fillList("text-list", "text-empty", analysis.text, renderText);
    fillList("shape-list", "shape-empty", analysis.shapes, renderShape);
    fillList("legend-list", "legend-empty", analysis.legend, (item) => renderLegend(item, colors));
    fillList("region-list", null, analysis.regions, (region) => renderRegion(region, colors));
    fillPairs("pair-list", "pair-empty", analysis, pairs, groups);
    document.getElementById("image-type").textContent =
      `Image type: ${analysis.image_type.replace("_", " ")}.`;
  }

  /** Each image's text alternative: the view, the local summary, and the AI summary if any. */
  function updateAlternatives(state) {
    const parts = [state.analysis.summary];
    if (state.interpretationSummary) {
      parts.push(`AI summary: ${state.interpretationSummary}`);
    }
    const summary = parts.join(" ");
    document.getElementById("base-image").alt = `Original view. ${summary}`;
    const name = state.overlay ? "Enhanced view with patterns" : "Enhanced view";
    document.getElementById("top-image").alt = `${name}. ${summary}`;
  }

  function updateEnhancedImage(state) {
    const view = state.overlay ? "overlay" : "enhanced";
    document.getElementById("top-image").src = imageUrl(state, view, state.strength / 100);
    const query = new URLSearchParams();
    ChromaSense.profile.addProfileTo(query, state.profile);
    query.append("strength", String(state.strength / 100));
    document.getElementById("download-link").href =
      `/api/images/${state.imageId}/export?${query}`;
    updateAlternatives(state);
  }

  function showResults(state) {
    const noCvd = state.profile.type === "none";
    const top = document.getElementById("top-image");
    document.getElementById("base-image").src = imageUrl(state, "original");
    document.getElementById("analysis-summary").textContent = state.analysis.summary;
    document.getElementById("best-effort-message").hidden =
      state.analysis.image_type !== "photograph";
    document.getElementById("no-cvd-message").hidden = !noCvd;
    document.getElementById("enhancement-controls").hidden = noCvd;
    document.getElementById("no-enhancement-message").hidden =
      noCvd || state.enhancementNeeded;
    const remaining = document.getElementById("remaining-pairs");
    remaining.hidden = noCvd || !state.enhancementNeeded;
    remaining.textContent = remaining.hidden
      ? ""
      : `Enhancement checked: ${state.remainingPairCount} of ${state.pairs.length} confusable pairs remain.`;
    top.hidden = noCvd;
    if (!noCvd) {
      updateEnhancedImage(state);
    }
    updateAlternatives(state);
    fillLocalResults(state);
    document.getElementById("simulator-link").href = `/simulator?image_id=${state.imageId}`;
  }

  function bindControls(state) {
    const compare = document.getElementById("compare-slider");
    const top = document.getElementById("top-image");
    const applyCompare = () => {
      top.style.clipPath = `inset(0 ${100 - Number(compare.value)}% 0 0)`;
      document.getElementById("compare-value").textContent = compare.value;
    };
    compare.addEventListener("input", applyCompare);
    applyCompare();

    const strength = document.getElementById("strength-slider");
    const refresh = ChromaSense.debounce(() => {
      updateEnhancedImage(state);
      ChromaSense.announce(`Enhancement strength is ${state.strength} percent.`);
    }, 250);
    strength.addEventListener("input", () => {
      state.strength = Number(strength.value);
      document.getElementById("strength-value").textContent = strength.value;
      refresh();
    });

    document.getElementById("overlay-toggle").addEventListener("change", (event) => {
      state.overlay = event.target.checked;
      updateEnhancedImage(state);
      ChromaSense.announce(event.target.checked ? "Patterns are on." : "Patterns are off.");
    });
  }

  async function loadState(imageId, profile) {
    const analysisResponse = await fetch(`/api/images/${imageId}/analysis`);
    if (!analysisResponse.ok) {
      throw new Error(await ChromaSense.errorMessage(analysisResponse));
    }
    const { analysis } = await analysisResponse.json();
    const pairsResponse = await fetch(`/api/images/${imageId}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(ChromaSense.profile.profileBody(profile)),
    });
    if (!pairsResponse.ok) {
      throw new Error(await ChromaSense.errorMessage(pairsResponse));
    }
    return { analysis, ...(await pairsResponse.json()) };
  }

  function showFailure(message) {
    const failure = document.getElementById("workspace-error");
    failure.textContent = message;
    failure.hidden = false;
    ChromaSense.announce(`The analysis pipeline failed. ${message}`);
  }

  /** Start a workspace, from a full page visit or after an upload placed it in the home page. */
  ChromaSense.startWorkspace = async function startWorkspace(root, uploadResult) {
    const holder = root.querySelector("#workspace");
    if (!holder) {
      return;
    }
    const imageId = holder.dataset.imageId;
    const profile = ChromaSense.profile.get() || { type: "none" };
    let loaded = uploadResult;
    if (!loaded) {
      ChromaSense.announce("Loading the analysis pipeline results.");
      try {
        loaded = await loadState(imageId, profile);
      } catch (error) {
        showFailure(error.message);
        return;
      }
    }
    const state = {
      imageId,
      profile,
      analysis: loaded.analysis,
      pairs: loaded.pairs,
      groups: loaded.groups,
      remainingPairCount: loaded.remaining_pair_count,
      enhancementNeeded: loaded.enhancement_needed,
      strength: 100,
      overlay: false,
      interpretationSummary: "",
    };
    showResults(state);
    bindControls(state);
    ChromaSense.colorPoint.start(state);
    ChromaSense.aiPanel.start(state);
    ChromaSense.speech.startControls(root);
    ChromaSense.speech.newResult(document.getElementById("local-results").innerText);
    if (!uploadResult) {
      ChromaSense.announce("Analysis pipeline results loaded.");
    }
  };

  ChromaSense.workspace = {
    colorName,
    colorsById,
    element,
    fillList,
    fillPairs,
    flagged,
    renderLegend,
    renderShape,
    renderText,
    swatch,
    updateAlternatives,
  };

  document.addEventListener("DOMContentLoaded", () => {
    if (document.querySelector("main > #workspace")) {
      ChromaSense.startWorkspace(document.getElementById("main"));
    }
  });
})();
