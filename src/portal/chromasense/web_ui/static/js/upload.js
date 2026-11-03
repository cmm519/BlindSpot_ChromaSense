"use strict";
window.ChromaSense = window.ChromaSense || {};

(function setUpUpload() {
  let pendingFile = null;

  function showError(message) {
    const element = document.getElementById("upload-error");
    element.textContent = message;
    element.hidden = !message;
  }

  /** Keep the image ID in the links, so that the user can return to the image. */
  function keepImageInLinks(imageId) {
    document.querySelectorAll("a[data-keep-image]").forEach((link) => {
      const url = new URL(link.href);
      url.searchParams.set("image_id", imageId);
      link.href = `${url.pathname}${url.search}`;
    });
  }

  async function placeWorkspace(result) {
    const response = await fetch(`/workspace/${result.image_id}`);
    if (!response.ok) {
      throw new Error("The image workspace could not be opened.");
    }
    const page = new DOMParser().parseFromString(await response.text(), "text/html");
    const section = document.getElementById("workspace-section");
    section.replaceChildren(...page.querySelector("main").childNodes);
    section.hidden = false;
    history.pushState({ imageId: result.image_id }, "", `/workspace/${result.image_id}`);
    document.dispatchEvent(new Event("workspace-placed"));
    keepImageInLinks(result.image_id);
    await ChromaSense.startWorkspace(section, result);
  }

  async function upload(file, profile) {
    showError("");
    ChromaSense.announce("Uploading the image, and starting the analysis pipeline.");
    const form = new FormData();
    form.append("file", file);
    ChromaSense.profile.addProfileTo(form, profile);
    try {
      const response = await fetch("/api/images", { method: "POST", body: form });
      if (!response.ok) {
        const message = await ChromaSense.errorMessage(response);
        showError(message);
        ChromaSense.announce(`Upload failed. The analysis pipeline did not start. ${message}`);
        return;
      }
      const result = await response.json();
      await placeWorkspace(result);
      ChromaSense.announce("Upload finished. Analysis pipeline finished. The results are below.");
    } catch (error) {
      const message = "The upload could not reach the server. Try again.";
      showError(message);
      ChromaSense.announce(`Upload failed. ${message}`);
    }
  }

  function askForProfile(file) {
    pendingFile = file;
    const dialog = document.getElementById("profile-dialog");
    document.getElementById("profile-dialog-error").hidden = true;
    dialog.showModal();
  }

  function startUpload(file) {
    if (!file) {
      return;
    }
    const profile = ChromaSense.profile.get();
    if (profile) {
      upload(file, profile);
    } else {
      askForProfile(file);
    }
  }

  function startDialog() {
    const dialog = document.getElementById("profile-dialog");
    const fileInput = document.getElementById("file-input");
    const fields = ChromaSense.profile.bindFields("prompt", null);

    const finish = () => {
      dialog.close();
      fileInput.focus();
    };

    document.getElementById("profile-dialog-form").addEventListener("submit", (event) => {
      event.preventDefault();
      const choice = fields.selected();
      if (!choice) {
        document.getElementById("profile-dialog-error").hidden = false;
        return;
      }
      const profile = ChromaSense.profile.save(choice.value, Number(fields.slider.value));
      const file = pendingFile;
      pendingFile = null;
      finish();
      upload(file, profile);
    });

    const cancel = () => {
      pendingFile = null;
      fileInput.value = "";
      ChromaSense.announce("Upload canceled.");
    };
    document.getElementById("profile-dialog-cancel").addEventListener("click", () => {
      cancel();
      finish();
    });
    dialog.addEventListener("cancel", (event) => {
      event.preventDefault();
      cancel();
      finish();
    });
  }

  function startHome() {
    const fileInput = document.getElementById("file-input");
    if (!fileInput) {
      return;
    }
    const zone = document.getElementById("drop-zone");
    startDialog();

    fileInput.addEventListener("change", () => startUpload(fileInput.files[0]));

    ["dragenter", "dragover"].forEach((name) =>
      zone.addEventListener(name, (event) => {
        event.preventDefault();
        zone.classList.add("is-over");
      }),
    );
    zone.addEventListener("dragleave", () => zone.classList.remove("is-over"));
    zone.addEventListener("drop", (event) => {
      event.preventDefault();
      zone.classList.remove("is-over");
      startUpload(event.dataTransfer.files[0]);
    });

    document.addEventListener("paste", (event) => {
      const item = [...event.clipboardData.items].find((entry) => entry.type.startsWith("image/"));
      if (item) {
        event.preventDefault();
        startUpload(item.getAsFile());
      }
    });

    // Back and Forward cross between the home page and a placed workspace. A skip link
    // changes only the hash, and it must not reload the page.
    let currentPath = window.location.pathname;
    document.addEventListener("workspace-placed", () => {
      currentPath = window.location.pathname;
    });
    window.addEventListener("popstate", () => {
      if (window.location.pathname !== currentPath) {
        window.location.reload();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", startHome);
})();
