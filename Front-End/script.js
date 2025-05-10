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

  // Universal Dropzone for both Hide and Reveal
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
  // ✅ Show preview of extracted image in Reveal page
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


  // Hide page logic
  if (hideInput) {
    hideInput.addEventListener("change", function () {
      const file = this.files[0];
      if (!file) return;

      if (document.getElementById("previewImage").style.display === "block") {
        if (!confirm("An image is already loaded. Do you want to replace it?")) return;
      }

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
        showToast("⚠️ Image too large or unsupported. Click 'Fix Image'", true);
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

  // Encrypt & Hide
  const combinedBtn = document.getElementById("encryptAndHideBtn");
  if (combinedBtn) {
    combinedBtn.addEventListener("click", async () => {
      const text = document.getElementById("textInput").value.trim();
      const key = document.getElementById("keyInput").value.trim();
      const algo = document.getElementById("encryptionSelect").value;
      const file = hideInput.files[0];
      const layers = document.getElementById("layerSelect").value;

      if (!file) return showToast("🖼️ Please choose an image", true);
      if (!text) return showToast("✉️ Please enter a message", true);
      if (algo !== "none" && !key) return showToast("🔑 Please enter encryption key", true);

      let message = text;
      if (algo !== "none") {
        try {
          const res = await fetch("/encrypt", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, key, algorithm: algo })
          });
          const data = await res.json();
          if (!data.result) return showToast("❌ Encryption failed", true);
          message = data.result;
        } catch (error) {
          console.error("Encryption error:", error);
          return showToast("❌ Encryption request error", true);
        }
      }

      const formData = new FormData();
      formData.append("image", file);
      formData.append("message", message);
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

  // Reveal Extract
  const extractBtn = document.getElementById("extractBtn");
  if (extractBtn) {
    extractBtn.addEventListener("click", () => {
      const file = revealInput.files[0];
      const layers = document.getElementById("layerSelect").value;
      if (!file) return showToast("🖼️ Select image to extract", true);

      const formData = new FormData();
      formData.append("image", file);
      formData.append("layers", layers);

      fetch("/extract", { method: "POST", body: formData })
        .then(res => res.json())
        .then(data => {
          if (data.result) {
            document.getElementById("textToDecrypt").value = data.result;
            showToast("✅ Message extracted!");
          } else {
            showToast("❌ " + (data.error || "No hidden message found"), true);
          }
        })
        .catch(() => showToast("❌ Extraction error", true));
    });
  }

  // Reveal Decrypt
  const decryptBtn = document.getElementById("decryptBtn");
  if (decryptBtn) {
    decryptBtn.addEventListener("click", () => {
      const text = document.getElementById("textToDecrypt").value.trim();
      const key = document.getElementById("keyToDecrypt").value.trim();
      const algo = document.getElementById("decryptAlgo").value;
      if (!text || !key) return showToast("❗ Provide both text and key", true);

      fetch("/decrypt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, key, algorithm: algo })
      })
      .then(res => res.json())
      .then(data => {
        if (data.result) {
          document.getElementById("textToDecrypt").value = data.result;
          showToast("✅ Message decrypted!");
        } else {
          showToast("❌ Decryption failed", true);
        }
      })
      .catch(() => showToast("❌ Decryption error", true));
    });
  }

});
