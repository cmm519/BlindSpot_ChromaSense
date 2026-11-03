"use strict";
window.ChromaSense = window.ChromaSense || {};

(function setUpProfile() {
  const STORAGE_KEY = "chromasense.profile";
  const NAMES = {
    protan: "protan",
    deutan: "deutan",
    tritan: "tritan",
    achromatopsia: "achromatopsia",
    none: "no CVD",
  };

  function getProfile() {
    try {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY));
      return stored && NAMES[stored.type] ? stored : null;
    } catch (error) {
      return null;
    }
  }

  function saveProfile(type, severity) {
    const profile = { type, updatedAt: new Date().toISOString() };
    if (type !== "none") {
      profile.severity = severity;
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
    return profile;
  }

  /** Add the profile to a query string or form. With no CVD, no severity is sent. */
  function addProfileTo(target, profile) {
    const active = profile || getProfile() || { type: "none" };
    const add = (name, value) => target.append(name, value);
    add("cvd_type", active.type);
    if (active.type !== "none") {
      add("severity", String(active.severity));
    }
    return target;
  }

  function profileBody(profile) {
    const active = profile || getProfile() || { type: "none" };
    return active.type === "none"
      ? { cvd_type: "none" }
      : { cvd_type: active.type, severity: active.severity };
  }

  /** Connect a set of profile fields, and show the given profile in them. */
  function bindFields(prefix, profile, onChange) {
    const radios = [...document.querySelectorAll(`input[name="${prefix}-type"]`)];
    const slider = document.getElementById(`${prefix}-severity`);
    const output = document.getElementById(`${prefix}-severity-value`);
    if (!radios.length || !slider) {
      return null;
    }

    const selected = () => radios.find((radio) => radio.checked);
    const sync = () => {
      const current = selected();
      slider.disabled = Boolean(current) && current.value === "none";
      output.textContent = slider.disabled ? "Not used with no CVD" : slider.value;
    };

    if (profile) {
      const match = radios.find((radio) => radio.value === profile.type);
      if (match) {
        match.checked = true;
      }
      if (profile.severity !== undefined) {
        slider.value = String(profile.severity);
      }
    }
    sync();

    const changed = () => {
      sync();
      if (onChange && selected()) {
        onChange(selected().value, Number(slider.value));
      }
    };
    radios.forEach((radio) => radio.addEventListener("change", changed));
    slider.addEventListener("input", changed);
    return { selected, slider };
  }

  function startSettingsForm() {
    if (!document.getElementById("profile-form")) {
      return;
    }
    bindFields("settings", getProfile(), (type, severity) => {
      saveProfile(type, severity);
      const detail = type === "none" ? NAMES[type] : `${NAMES[type]}, severity ${severity}`;
      ChromaSense.announce(`Profile saved: ${detail}.`);
    });
  }

  ChromaSense.profile = {
    addProfileTo,
    bindFields,
    get: getProfile,
    name: (type) => NAMES[type],
    profileBody,
    save: saveProfile,
  };
  document.addEventListener("DOMContentLoaded", startSettingsForm);
})();
