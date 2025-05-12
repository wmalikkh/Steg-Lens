document.addEventListener("DOMContentLoaded", () => {

  function showToast(message, isError = false) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.className = "toast" + (isError ? " error" : "");
    toast.style.display = "block";
    setTimeout(() => {
      toast.style.display = "none";
    }, 3000);
  }

  const dropzone = document.getElementById("dropzone");
  const hideInput = document.getElementById("imageInput");
  const revealInput = document.getElementById("extractInput");

  if (dropzone && (hideInput || revealInput)) {
    const input = hideInput || revealInput;
    dropzone.onclick = () => input.click();
    dropzone.ondragover = e => { e.preventDefault(); dropzone.classList.add("hover"); };
    dropzone.ondragleave = () => dropzone.classList.remove("hover");
    dropzone.ondrop = e => {
      e.preventDefault();
      dropzone.classList.remove("hover");
      input.files = e.dataTransfer.files;
      input.dispatchEvent(new Event("change"));
    };
  }

  if (revealInput) {
    revealInput.addEventListener("change", function () {
      const file = this.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = e => {
        const preview = document.getElementById("revealPreview");
        if (preview) {
          preview.src = e.target.result;
          preview.style.display = "block";
        }
      };
      reader.readAsDataURL(file);
    });
  }

  if (hideInput) {
    hideInput.addEventListener("change", function () {
      const file = this.files[0];
      if (!file) return;
      const maxSize = 10 * 1024 * 1024;
      const allowedTypes = ["image/png", "image/jpeg", "image/gif"];
      const editBtn = document.getElementById("editBtn");

      const reader = new FileReader();
      reader.onload = e => {
        document.getElementById("previewImage").src = e.target.result;
        document.getElementById("previewImage").style.display = "block";
      };
      reader.readAsDataURL(file);

      if (file.size > maxSize || !allowedTypes.includes(file.type)) {
        if (editBtn) editBtn.style.display = "inline-block";
        showToast("⚠️ Only PNG, JPEG, or GIF allowed. Max size is 10MB. Click 'Fix Image' to convert.", true);
      } else {
        if (editBtn) editBtn.style.display = "none";
      }
    });
  }

  const editBtn = document.getElementById("editBtn");
  if (editBtn) {
    editBtn.addEventListener("click", () => {
      const file = hideInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function (e) {
        const img = new Image();
        img.onload = function () {
          const canvas = document.createElement("canvas");
          const scale = 800 / img.width;
          canvas.width = 800;
          canvas.height = img.height * scale;
          const ctx = canvas.getContext("2d");
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          canvas.toBlob(blob => {
            const newFile = new File([blob], "converted.png", { type: "image/png" });
            const dt = new DataTransfer();
            dt.items.add(newFile);
            hideInput.files = dt.files;
            document.getElementById("previewImage").src = URL.createObjectURL(newFile);
            showToast("✅ Image fixed and converted to PNG.");
            editBtn.style.display = "none";
          }, "image/png", 0.8);
        };
        img.src = e.target.result;
      };
      reader.readAsDataURL(file);
    });
  }

  const encryptBtn = document.getElementById("encryptBtn");
  if (encryptBtn) {
    encryptBtn.addEventListener("click", () => {
      const text = document.getElementById("textInput").value.trim();
      const key = document.getElementById("keyInput").value.trim();
      const algo = document.querySelector('input[name="algo"]:checked').value;

      if (!text) return showToast("⚠️ Please enter a message", true);
      if (algo !== "none" && !key) return showToast("🛡️ Please provide an encryption key", true);

      if (algo === "none") {
        document.getElementById("messageInput").value = text;
        return showToast("✅ Message ready to hide!");
      }

      fetch("/encrypt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, key, algorithm: algo })
      })
      .then(res => res.json())
      .then(data => {
        if (data.result) {
          document.getElementById("messageInput").value = data.result;
          showToast("✅ Message encrypted!");
        } else {
          showToast("❌ Encryption failed: " + (data.error || "Unknown error"), true);
        }
      })
      .catch(() => showToast("🚨 Encryption failed", true));
    });
  }

  const combinedBtn = document.getElementById("encryptAndHideBtn");
  if (combinedBtn) {
    combinedBtn.addEventListener("click", async () => {
      const file = hideInput.files[0];
      const text = document.getElementById("textInput").value.trim();
      const message = document.getElementById("messageInput").value.trim() || text;
      const layers = document.getElementById("layerSelect")?.value || "1";

      if (!file) return showToast("🖼️ Please choose an image", true);
      if (!message && !document.getElementById("textFileInput").files[0]) return showToast("✉️ Please enter a message or upload a text file", true);

      const formData = new FormData();
      formData.append("image", file);

      // ✅ new logic: support either text OR file
      const textFile = document.getElementById("textFileInput").files[0];
      if (textFile && !text) {
        formData.append("text_file", textFile);
      } else {
        formData.append("message", message);
      }

      formData.append("layers", layers);

      try {
        const res = await fetch("/hide", { method: "POST", body: formData });
        const ext = res.headers.get("X-Image-Extension") || "png";
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);

        document.getElementById("previewImage").src = url;
        document.getElementById("previewImage").style.display = "block";

        if ('showSaveFilePicker' in window) {
          const handle = await window.showSaveFilePicker({
            suggestedName: `steg-image.${ext}`,
            types: [{ description: "Image File", accept: { [blob.type]: [`.${ext}`] } }]
          });
          const writable = await handle.createWritable();
          await writable.write(blob);
          await writable.close();
          showToast("✅ Image saved!");
        } else {
          const a = document.createElement("a");
          a.href = url;
          a.download = `steg-image.${ext}`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          showToast("ℹ️ Downloaded to default folder.");
        }
      } catch (e) {
        console.error(e);
        showToast("❌ Hiding failed", true);
      }
    });
  }

  const extractBtn = document.getElementById("extractBtn");
  if (extractBtn) {
    extractBtn.addEventListener("click", () => {
      const file = revealInput.files[0];
      if (!file) return showToast("🖼️ Select image to extract", true);

      const formData = new FormData();
      formData.append("image", file);

      fetch("/extract", { method: "POST", body: formData })
      .then(res => res.json())
      .then(data => {
        if (data.result) {
          document.getElementById("extractedResult").innerText = data.result;
          showToast("✅ Message extracted!");
        } else {
          showToast("❌ " + (data.error || "No hidden message found"), true);
        }
      })
      .catch(() => showToast("❌ Extraction error", true));
    });
  }

  const decryptBtn = document.getElementById("decryptBtn");
  if (decryptBtn) {
    decryptBtn.addEventListener("click", () => {
      const text = document.getElementById("textToDecrypt").value.trim();
      const key = document.getElementById("keyToDecrypt").value.trim();
      const algo = document.querySelector('input[name="algo-decrypt"]:checked')?.value || document.getElementById("decryptAlgo").value;

      if (!text || !key) return showToast("❗ Provide both text and key", true);

      fetch("/decrypt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, key, algorithm: algo })
      })
      .then(res => res.json())
      .then(data => {
        if (data.result) {
          document.getElementById("decryptedResult").innerText = data.result;
          showToast("✅ Message decrypted!");
        } else {
          showToast("❌ Decryption failed", true);
        }
      })
      .catch(() => showToast("❌ Decryption error", true));
    });
  }

});
