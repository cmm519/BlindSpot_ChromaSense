"use strict";
window.ChromaSense = window.ChromaSense || {};

(function setUpColorPoint() {
  const STEP_SHARE = 0.01;

  function start(state) {
    const area = document.getElementById("point-area");
    const mark = document.getElementById("point-mark");
    const { width, height, regions } = state.analysis;
    const point = { x: Math.floor(width / 2), y: Math.floor(height / 2) };
    let regionIndex = -1;
    let requestNumber = 0;

    function placeMark() {
      mark.hidden = false;
      const left = (100 * point.x) / width;
      const top = (100 * point.y) / height;
      mark.style.left = `${left}%`;
      mark.style.top = `${top}%`;
      document.getElementById("point-position").textContent =
        `Point at ${Math.round(left)} percent from the left and ${Math.round(top)} percent from the top.`;
    }

    function showColor(result) {
      const { color } = result;
      const holder = document.getElementById("color-result");
      const { element, swatch } = ChromaSense.workspace;
      const nameLine = element("p");
      nameLine.append(swatch(color.rgb));
      nameLine.append(`Color: ${color.name}. Color family: ${color.family}.`);
      const values = element(
        "p",
        "",
        `HEX ${color.hex}. RGB ${color.rgb.join(", ")}. ` +
          `HSL ${color.hsl[0]} degrees, ${color.hsl[1]} percent, ${color.hsl[2]} percent.`,
      );
      const parts = [nameLine, values];
      if (result.simulated_rgb) {
        const simulated = element("p");
        simulated.id = "simulated-color";
        simulated.append(swatch(result.simulated_rgb));
        simulated.append(
          `Under your profile, this appears as ${result.simulated_hex}, ` +
            `RGB ${result.simulated_rgb.join(", ")}.`,
        );
        parts.push(simulated);
      }
      holder.replaceChildren(...parts);
    }

    /** Identify the color at the point, and ignore an answer that a newer move replaced. */
    async function identify(describe) {
      placeMark();
      requestNumber += 1;
      const thisRequest = requestNumber;
      const query = new URLSearchParams({ x: String(point.x), y: String(point.y) });
      ChromaSense.profile.addProfileTo(query, state.profile);
      let response;
      try {
        response = await fetch(`/api/images/${state.imageId}/color?${query}`);
      } catch (error) {
        ChromaSense.announce("The color could not be identified. The server did not answer.");
        return;
      }
      if (thisRequest !== requestNumber) {
        return;
      }
      if (!response.ok) {
        ChromaSense.announce(`The color could not be identified. ${await ChromaSense.errorMessage(response)}`);
        return;
      }
      const result = await response.json();
      showColor(result);
      const message = describe(result.color);
      ChromaSense.announce(message);
      ChromaSense.speech.newResult(document.getElementById("color-result").innerText);
    }

    const describePoint = (color) => `${color.name}, ${color.hex}.`;

    function moveByKeys(key) {
      const stepX = Math.max(1, Math.round(width * STEP_SHARE));
      const stepY = Math.max(1, Math.round(height * STEP_SHARE));
      const moves = {
        ArrowLeft: [-stepX, 0],
        ArrowRight: [stepX, 0],
        ArrowUp: [0, -stepY],
        ArrowDown: [0, stepY],
      };
      const [moveX, moveY] = moves[key];
      point.x = Math.min(width - 1, Math.max(0, point.x + moveX));
      point.y = Math.min(height - 1, Math.max(0, point.y + moveY));
      identify(describePoint);
    }

    function moveToRegion(direction) {
      if (!regions.length) {
        ChromaSense.announce("This image has no detected regions.");
        return;
      }
      regionIndex = (regionIndex + direction + regions.length) % regions.length;
      const region = regions[regionIndex];
      point.x = Math.min(width - 1, Math.round(region.center_x));
      point.y = Math.min(height - 1, Math.round(region.center_y));
      const number = regionIndex + 1;
      identify(
        (color) =>
          `Region ${number} of ${regions.length}. ${color.name}. ` +
          `Size ${region.width} by ${region.height} pixels. ` +
          `Location ${Math.round((100 * region.center_x) / width)} percent from the left, ` +
          `${Math.round((100 * region.center_y) / height)} percent from the top.`,
      );
    }

    area.addEventListener("click", (event) => {
      const box = area.getBoundingClientRect();
      const scaleX = width / box.width;
      const scaleY = height / box.height;
      point.x = Math.min(width - 1, Math.max(0, Math.floor((event.clientX - box.left) * scaleX)));
      point.y = Math.min(height - 1, Math.max(0, Math.floor((event.clientY - box.top) * scaleY)));
      identify(describePoint);
    });

    area.addEventListener("keydown", (event) => {
      if (event.key.startsWith("Arrow")) {
        event.preventDefault();
        moveByKeys(event.key);
      } else if (event.key === "n" || event.key === "N") {
        event.preventDefault();
        moveToRegion(1);
      } else if (event.key === "p" || event.key === "P") {
        event.preventDefault();
        moveToRegion(-1);
      }
    });
  }

  ChromaSense.colorPoint = { start };
})();
