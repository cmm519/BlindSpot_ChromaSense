"use strict";
window.ChromaSense = window.ChromaSense || {};

/** Put a message in the one shared live region. Focus never moves. */
ChromaSense.announce = function announce(message) {
  const region = document.getElementById("live-region");
  if (!region) {
    return;
  }
  // A screen reader ignores unchanged text, so a repeated message must differ.
  region.textContent = region.textContent === message ? `${message} ` : message;
};

/** Read the message from a failed API response. */
ChromaSense.errorMessage = async function errorMessage(response) {
  try {
    const body = await response.json();
    return body.error.message;
  } catch (error) {
    return `The server answered with status ${response.status}.`;
  }
};

ChromaSense.debounce = function debounce(action, waitMs) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => action(...args), waitMs);
  };
};
