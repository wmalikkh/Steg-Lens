let decryptClicked = false;

// 🔐 Encrypt Text and save to .txt file
document.getElementById("encryptBtn").addEventListener("click", function () {
  const text = document.getElementById("textInput").value;
  const algorithm = document.getElementById("encryptionType").value;
  let key = prompt("🔑 Enter key:\nAES: 16 chars or HEX (32 digits)\n3DES: 21 chars or HEX (42 digits)");
  let rawKey = key;

  if (!text || !key) return showToast("❌ Please provide both text and key.", "error");

  const selectedAlgorithm = algorithm === "aes" ? "AES-128" : "3DES";
  const requiredBytes = selectedAlgorithm === "AES-128" ? 16 : 21;

  if (isHexKey(key, requiredBytes)) {
    try {
      rawKey = atob(hexToBase64(key));
    } catch {
      return showToast("❌ Invalid HEX key format.", "error");
    }
  } else if (key.length !== requiredBytes) {
    return showToast("❌ Invalid key. Must be ASCII with correct length or HEX.", "error");
  }

  fetch("http://127.0.0.1:5000/encrypt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, key: rawKey, algorithm: selectedAlgorithm })
  })
    .then(res => res.json())
    .then(data => {
      if (data.result) {
        sessionStorage.setItem("encryptedText", data.result);
        const blob = new Blob([data.result], { type: "text/plain" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "encrypted_text.txt";
        link.click();
        showToast("✅ Text encrypted and saved!");
      } else showToast(data.error || "Encryption failed.", "error");
    })
    .catch(() => showToast("❌ Could not connect to server.", "error"));
});

// 🔓 Decrypt using resultOutput only in Extract (not here)
document.getElementById("decryptBtn").addEventListener("click", function () {
  document.getElementById("extractBtn").style.display = "inline-block";

  const inputValue = document.getElementById("resultOutput")?.value.trim();

  if (!decryptClicked) {
    decryptClicked = true;
    showToast("📥 Now click 'Extract Hidden Text' to load the encrypted message.");
    return;
  }

  if (!inputValue) {
    showToast("ℹ️ Please extract hidden message first before decrypting.", "error");
    return;
  }

  const algorithm = document.getElementById("encryptionType").value;
  const selectedAlgorithm = algorithm === "aes" ? "AES-128" : "3DES";
  const requiredBytes = selectedAlgorithm === "AES-128" ? 16 : 21;

  let key = prompt("Enter decryption key:");
  if (!key) return showToast("❌ No key provided.", "error");

  let rawKey = key;

  if (isHexKey(key, requiredBytes)) {
    try {
      rawKey = atob(hexToBase64(key));
    } catch {
      return showToast("❌ Invalid HEX key format.", "error");
    }
  } else if (key.length !== requiredBytes) {
    return showToast("❌ Invalid key. Must be ASCII with correct length or HEX.", "error");
  }

  fetch("http://127.0.0.1:5000/decrypt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: inputValue, key: rawKey, algorithm: selectedAlgorithm })
  })
    .then(res => res.json())
    .then(data => {
      if (data.result) {
        document.getElementById("decryptedText").innerText = data.result;
        document.getElementById("decryptedOutput").style.display = "block";
        showToast("🔓 Decrypted successfully!");
      } else {
        showToast(data.error || "❌ Decryption failed.", "error");
      }
    })
    .catch(() => showToast("❌ Could not connect to server.", "error"));
});

// 📋 Copy decrypted text
document.getElementById("copyDecryptedBtn").addEventListener("click", () => {
  const text = document.getElementById("decryptedText").innerText;
  navigator.clipboard.writeText(text);
  showToast("📋 Decrypted text copied!");
});

// 🖼️ Hide Encrypted Text (with format detection)
document.getElementById("hideBtn").addEventListener("click", function () {
  const image = document.getElementById("imageInput").files[0];
  const message = sessionStorage.getItem("encryptedText");
  if (!image || !message) return showToast("❌ Missing image or encrypted text.", "error");

  const formData = new FormData();
  formData.append("image", image);
  formData.append("message", message);

  fetch("http://127.0.0.1:5000/hide", {
    method: "POST",
    body: formData,
  })
    .then(res => {
      const ext = res.headers.get("X-Image-Extension") || "png";
      sessionStorage.setItem("imageExt", ext);
      return res.blob();
    })
    .then(blob => {
      const url = URL.createObjectURL(blob);
      sessionStorage.setItem("encryptedImage", url);
      showToast("🖼️ Message hidden inside image!");
      document.getElementById("downloadBtn").style.display = "inline-block";
    })
    .catch(() => showToast("❌ Hiding failed.", "error"));
});

// 🔍 Extract Hidden Text
document.getElementById("extractBtn").addEventListener("click", function () {
  const image = document.getElementById("imageInput").files[0];
  if (!image) return showToast("❌ Please select an image to extract from.", "error");

  const formData = new FormData();
  formData.append("image", image);

  fetch("http://127.0.0.1:5000/extract", {
    method: "POST",
    body: formData,
  })
    .then(res => res.json())
    .then(data => {
      if (data.result) {
        document.getElementById("resultBox").style.display = "block";
        document.getElementById("resultOutput").value = data.result;
        showToast("🔍 Text extracted!");
      } else {
        showToast("❌ Extraction failed. No hidden text found.", "error");
      }
    })
    .catch(() => showToast("❌ Extraction failed due to connection error.", "error"));
});

// 📥 Download Image with correct extension
document.getElementById("downloadBtn").addEventListener("click", () => {
  const url = sessionStorage.getItem("encryptedImage");
  const ext = sessionStorage.getItem("imageExt") || "png";
  const link = document.createElement("a");
  link.href = url;
  link.download = `steg-image.${ext}`;
  link.click();
  showToast("📥 Download started!");
});

// 📸 Preview Image
function previewImage(file) {
  const preview = document.getElementById("previewImage");
  const reader = new FileReader();
  reader.onload = function (e) {
    preview.src = e.target.result;
    preview.style.display = "block";
  };
  reader.readAsDataURL(file);
}

// ✅ Toast Notification
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerText = message;
  if (type === "error") {
    toast.style.backgroundColor = "#ff4f4f";
    toast.style.color = "#fff";
  }
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("hide");
    setTimeout(() => {
      toast.remove();
    }, 500);
  }, 3000);
}

// 🔍 HEX Key Check
function isHexKey(key, expectedBytes) {
  const hexRegex = /^[0-9a-fA-F]+$/;
  return hexRegex.test(key) && key.length === expectedBytes * 2;
}

function hexToBase64(hex) {
  return btoa(
    hex.match(/\w{2}/g).map((b) => String.fromCharCode(parseInt(b, 16))).join("")
  );
}

// 🎯 Toggle Sections
function toggleSection(id) {
  const sections = ["home", "about", "contact"];
  sections.forEach((sec) => {
    document.getElementById(sec).style.display = sec === id ? "block" : "none";
  });
}

// 🖱️ Drag & Drop Support
const dragArea = document.getElementById("dragDropArea");
const imageInput = document.getElementById("imageInput");

dragArea.addEventListener("dragover", function (e) {
  e.preventDefault();
  dragArea.style.backgroundColor = "#252525";
});
dragArea.addEventListener("dragleave", function () {
  dragArea.style.backgroundColor = "#1b1b1b";
});
dragArea.addEventListener("drop", function (e) {
  e.preventDefault();
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    imageInput.files = files;
    previewImage(files[0]);
    document.getElementById("imageReady").style.display = "block";
  }
});
imageInput.addEventListener("change", function () {
  if (imageInput.files.length > 0) {
    previewImage(imageInput.files[0]);
    document.getElementById("imageReady").style.display = "block";
  }
});

// 🌗 Toggle Light/Dark Mode
document.getElementById("toggleModeBtn").addEventListener("click", () => {
  document.body.classList.toggle("dark-mode");
});
