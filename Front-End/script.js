document.addEventListener("DOMContentLoaded", () => {
  function showPopup(message, isError = false) {
    if (Swal.getTimerLeft()) Swal.stopTimer();
    Swal.fire({
      icon: isError ? 'error' : 'success',
      title: isError ? 'Error' : 'Success',
      html: message.replace(/\n/g, "<br>"),
      confirmButtonText: 'OK',
      allowOutsideClick: false,
      allowEscapeKey: false
    });
  }

  const generateKeyBtn = document.getElementById("generateKeyBtn");
  if (generateKeyBtn) {
    generateKeyBtn.addEventListener("click", () => {
      const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()";
      let key = "";
      for (let i = 0; i < 16; i++) {
        key += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      document.getElementById("keyInput").value = key;
      showPopup("🔑 Random key generated");
    });
  }

  async function autoFixImage(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = e => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement("canvas");
          
          // تحديد الأبعاد الجديدة بناءً على حجم الملف
          let width = img.width;
          let height = img.height;
          
          if (file.size > 10 * 1024 * 1024) { // للصور الكبيرة (>10MB)
            const maxDimension = 2000;
            const ratio = Math.min(maxDimension / width, maxDimension / height);
            width = width * ratio;
            height = height * ratio;
          } 
          else if (file.size < 5 * 1024) { // للصور الصغيرة (<5KB)
            const minDimension = 500;
            const ratio = Math.max(minDimension / width, minDimension / height);
            width = width * ratio;
            height = height * ratio;
          }

          canvas.width = width;
          canvas.height = height;
          
          const ctx = canvas.getContext("2d");
          ctx.imageSmoothingQuality = "high";
          ctx.drawImage(img, 0, 0, width, height);
          
          canvas.toBlob(blob => {
            const newFile = new File([blob], file.name.replace(/\.[^/.]+$/, "") + ".png", { 
              type: "image/png",
              lastModified: new Date().getTime()
            });
            resolve(newFile);
          }, "image/png", 0.85);
        };
        img.onerror = () => reject(new Error("Image load failed"));
        img.src = e.target.result;
      };
      reader.onerror = () => reject(new Error("Read failed"));
      reader.readAsDataURL(file);
    });
  }

  const hideInput = document.getElementById("imageInput");
  const extractInput = document.getElementById("extractInput");
  const dropzone = document.getElementById("dropzone");
  const changeImageBtn = document.getElementById("changeImageBtn");
  const previewId = hideInput ? "previewImage" : "revealPreview";
  const activeInput = hideInput || extractInput;

  const verifyBar = document.createElement("div");
  verifyBar.id = "verify-loading-bar";
  verifyBar.style.cssText = "width: 100%; height: 5px; background: #2400ff; position: absolute; top: 0; left: 0; z-index: 9999; display: none;";
  document.body.appendChild(verifyBar);

  function startVerifyBar() {
    verifyBar.style.display = "block";
    verifyBar.style.width = "0%";
    let progress = 0;
    verifyBar.interval = setInterval(() => {
      if (progress < 90) {
        progress += 10;
        verifyBar.style.width = `${progress}%`;
      }
    }, 200);
  }

  function stopVerifyBar() {
    clearInterval(verifyBar.interval);
    verifyBar.style.width = "100%";
    setTimeout(() => { verifyBar.style.display = "none"; }, 300);
  }

  function setupImageTrigger(button) {
    if (button && activeInput) {
      button.onclick = () => {
        Swal.fire({
          icon: 'info',
          title: 'Image Requirements',
          html: `We accept PNG, JPEG, GIF, BMP, or TIFF images under 10MB.<br>Unsupported formats will be converted to PNG.`,
          confirmButtonText: 'OK',
          showCancelButton: true,
          cancelButtonText: 'Cancel'
        }).then(result => {
          if (result.isConfirmed) activeInput.click();
        });
      };
    }
  }

  setupImageTrigger(dropzone);
  setupImageTrigger(changeImageBtn);

  if (dropzone) {
    dropzone.ondragover = e => {
      e.preventDefault();
      dropzone.classList.add("hover");
    };
    dropzone.ondragleave = () => dropzone.classList.remove("hover");
    dropzone.ondrop = e => {
      e.preventDefault();
      dropzone.classList.remove("hover");
      if (e.dataTransfer.files.length > 0) {
        activeInput.files = e.dataTransfer.files;
        activeInput.dispatchEvent(new Event("change"));
      }
    };
  }

  if (activeInput) {
    activeInput.addEventListener("change", async function () {
      let file = this.files[0];
      if (!file) return;

      const unsupportedTypes = ["video/", "audio/"];
      const convertableTypes = ["image/tiff", "image/bmp"];
      const allowedTypes = ["image/png", "image/jpeg", "image/gif", "image/bmp", "image/tiff"];
      
      if (unsupportedTypes.some(t => file.type.startsWith(t))) {
        return showPopup("❌ Unsupported file type. Please upload an image.", true);
      }

      const maxSize = 10 * 1024 * 1024;
      const needsFix = file.size > maxSize || !allowedTypes.includes(file.type) || file.size < 5 * 1024 || convertableTypes.includes(file.type);

      startVerifyBar();

      if (needsFix) {
        const confirmFix = await Swal.fire({
          icon: 'warning',
          title: file.size < 5 * 1024 ? 'Very Small Image' : 
                 file.size > maxSize ? 'Large Image' : 
                 convertableTypes.includes(file.type) ? 'Unsupported Format' : 'Image Needs Adjustment',
          html: file.size < 5 * 1024 ? 'This image is very small (<5KB).<br>Do you want to enlarge it automatically?' :
                file.size > maxSize ? 'This image is too large (>10MB).<br>Do you want to resize it automatically?' :
                convertableTypes.includes(file.type) ? 'This image format (BMP/TIFF) will be converted to PNG.<br>Do you want to proceed?' :
                'This image needs adjustment.<br>Do you want to fix it automatically?',
          confirmButtonText: 'Fix it',
          showCancelButton: true,
          cancelButtonText: 'Cancel'
        });

        if (!confirmFix.isConfirmed) {
          stopVerifyBar();
          return;
        }

        try {
          const fixedFile = await autoFixImage(file);
          const dt = new DataTransfer();
          dt.items.add(fixedFile);
          this.files = dt.files;
          file = fixedFile;
          showPopup("⚠️ Image processed: " + 
            (file.size < 5 * 1024 ? "Enlarged small image" :
             file.size > 10 * 1024 * 1024 ? "Resized large image" : 
             convertableTypes.includes(file.type) ? "Converted to PNG" : "Adjusted image"));
        } catch (e) {
          console.error("Auto-fix failed", e);
          stopVerifyBar();
          return showPopup("❌ Failed to process image", true);
        }
      }

      const reader = new FileReader();
      reader.onload = e => {
        const img = document.getElementById(previewId);
        img.src = e.target.result;
        img.style.display = "block";

        if (changeImageBtn) changeImageBtn.style.display = "inline-block";
      };
      reader.readAsDataURL(file);

      stopVerifyBar();
    });
  }

  const combinedBtn = document.getElementById("encryptAndHideBtn");
  if (combinedBtn) {
    combinedBtn.addEventListener("click", async () => {
      const file = hideInput.files[0];
      if (!file) return showPopup("🖼️ Please select an image", true);

      const text = document.getElementById("textInput").value.trim();
      const message = document.getElementById("messageInput").value.trim() || text;
      const layers = document.getElementById("layerSelect")?.value || "1";
      const encryption = document.getElementById("encryptionSelect").value;
      const key = document.getElementById("keyInput").value;

      if (!message && !document.getElementById("textFileInput").files[0]) {
        return showPopup("✉️ Please enter a message or upload a text file", true);
      }

      if (encryption !== "none" && !key) {
        return showPopup("🔑 Please enter an encryption key", true);
      }

      const formData = new FormData();
      formData.append("image", file);

      const textFile = document.getElementById("textFileInput").files[0];
      if (textFile && !text) {
        formData.append("text_file", textFile);
      } else {
        formData.append("message", message);
      }

      formData.append("layers", layers);
      formData.append("encryption", encryption !== "none" ? "true" : "false");
      formData.append("algorithm", encryption !== "none" ? encryption : "");
      formData.append("key", encryption !== "none" ? key : "");

      try {
        LoadingBar.start();
        const res = await fetch("/hide", { method: "POST", body: formData });
        if (!res.ok) throw new Error("Server rejected the image");

        const ext = res.headers.get("X-Image-Extension") || "png";
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);

        const preview = document.getElementById("previewImage");
        preview.src = url;
        preview.style.display = "block";

        showPopup(`💾 Image ready to save<br>${encryption !== "none" ? "🔒 Encrypted" : ""}`);

        if ('showSaveFilePicker' in window) {
          const handle = await window.showSaveFilePicker({
            suggestedName: `steg-image.${ext}`,
            types: [{ description: "Images", accept: { "image/*": [`.${ext}`] } }],
            excludeAcceptAllOption: true
          });
          const writable = await handle.createWritable();
          await writable.write(blob);
          await writable.close();
          showPopup("✅ Image saved successfully!");
        } else {
          const a = document.createElement("a");
          a.href = url;
          a.download = `steg-image.${ext}`;
          a.click();
          showPopup("⬇️ Downloaded using fallback");
        }
      } catch (err) {
        console.error(err);
        showPopup("❌ Hiding or saving failed", true);
      } finally {
        LoadingBar.stop();
      }
    });
  }

  const extractBtn = document.getElementById("extractBtn");
  if (extractBtn && extractInput) {
    extractBtn.addEventListener("click", async () => {
      const file = extractInput.files[0];
      if (!file) return showPopup("🖼️ Please select an image to extract from", true);

      extractBtn.disabled = true;
      extractBtn.textContent = "Processing...";
      LoadingBar.start();

      const formData = new FormData();
      formData.append("image", file);
      formData.append("decryption", "false");

      try {
        const res = await fetch("/extract", { method: "POST", body: formData });
        const contentType = res.headers.get("Content-Type") || "";
        if (!contentType.includes("application/json")) {
          throw new Error("❌ No hidden message found in this image.");
        }

        const data = await res.json();
        const output = document.getElementById("extractedResult");
        const extracted = data.result || data.message || data.extracted_data;
        if (!extracted || !extracted.trim()) {
         throw new Error("❌ No hidden message found in this image.");
        }
        if (data.is_encrypted) {
          const encryptedText = data.result || data.message || data.extracted_data;
          output.innerHTML = `<strong>Encrypted Message:</strong><br>${encryptedText || ''}`;
          document.getElementById("textToDecrypt").value = encryptedText;

          const key = document.getElementById("keyToDecrypt")?.value;
          const algorithm = document.getElementById("decryptAlgo")?.value || "AES-128";

          if (key) {
            const decryptionResult = await attemptDecryption(encryptedText, algorithm, key);
            if (!decryptionResult.error) {
              document.getElementById("decryptedResult").innerHTML =
                `<strong>Decrypted Message:</strong><br>${decryptionResult.result}`;
              showPopup("✅ Message extracted and decrypted successfully!");
            } else {
              showPopup(`🔒 ${decryptionResult.error}`, true);
            }
          } else {
            showPopup("🔒 Encrypted message detected. Enter a key to decrypt.");
          }
        } else {
          output.innerHTML = `<strong>Extracted Message:</strong><br>${data.result || data.message || data.extracted_data}`;
          showPopup("✅ Message extracted successfully!");
        }
      } catch (err) {
        console.error("Extraction error:", err);
        showPopup(`${err.message || "❌ Extraction failed"}`, true);
      } finally {
        extractBtn.disabled = false;
        extractBtn.textContent = "Extract Message";
        LoadingBar.stop();
      }
    });
  }

  async function attemptDecryption(encryptedText, algorithm, key) {
    try {
      const response = await fetch("/decrypt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: encryptedText, algorithm, key })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Decryption failed");
      }

      return await response.json();
    } catch (err) {
      console.error("Decryption error:", err);
      return { error: err.message || "Decryption failed" };
    }
  }

  const decryptBtn = document.getElementById("decryptBtn");
  if (decryptBtn) {
    decryptBtn.addEventListener("click", async () => {
      const encryptedText = document.getElementById("extractedResult").textContent
        .replace('Encrypted Message:', '')
        .trim();
      const key = document.getElementById("keyToDecrypt").value;
      const algorithm = document.getElementById("decryptAlgo").value;

      if (!encryptedText || !key) {
        return showPopup("❌ Please provide both encrypted text and decryption key", true);
      }

      try {
        LoadingBar.start();
        const decryptionResult = await attemptDecryption(encryptedText, algorithm, key);
        if (decryptionResult.error) throw new Error(decryptionResult.error);

        document.getElementById("decryptedResult").innerHTML =
          `<strong>Decrypted Message:</strong><br>${decryptionResult.result}`;
        showPopup("✅ Message decrypted successfully!");
      } catch (err) {
        console.error(err);
        showPopup(`❌ ${err.message || "Decryption failed"}`, true);
      } finally {
        LoadingBar.stop();
      }
    });
  }
});