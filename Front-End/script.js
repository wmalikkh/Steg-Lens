// Helper function to show a toast notification
function showToast(message, isError = false) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.className = "toast" + (isError ? " error" : "");
    toast.style.display = "block";
    setTimeout(() => {
        toast.style.display = "none";
    }, 3000);
}

// Encrypt and/or Hide Message
document.getElementById("encryptBtn").addEventListener("click", function () {
    const textInput = document.getElementById("textInput").value.trim();
    const keyInput = document.getElementById("keyInput").value.trim();
    const algo = document.querySelector('input[name="algo"]:checked').value;

    if (!textInput) {
        showToast("⚠️ Please write a message to encrypt or hide", true);
        return;
    }

    if (algo !== "none" && !keyInput) {
        showToast("🛡️ Encryption key is required when encryption is selected", true);
        return;
    }

    if (algo === "none") {
        document.getElementById("messageInput").value = textInput;
        showToast("✅ Message ready to hide!");
    } else {
        fetch("/encrypt", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: textInput, key: keyInput, algorithm: algo })
        })
        .then(response => response.json())
        .then(data => {
            if (data.result) {
                document.getElementById("messageInput").value = data.result;
                showToast("✅ Message encrypted successfully!");
            } else {
                showToast("❌ Failed to encrypt: " + (data.error || "Unknown error"), true);
            }
        })
        .catch(error => {
            console.error("Encryption error:", error);
            showToast("🚨 Encryption failed. Please try again.", true);
        });
    }
});

// Hide message into image
document.getElementById("hideBtn").addEventListener("click", function () {
    const fileInput = document.getElementById("imageInput");
    const messageInput = document.getElementById("messageInput");

    if (!fileInput.files.length) {
        showToast("🖼️ Please select an image first", true);
        return;
    }
    if (!messageInput.value.trim()) {
        showToast("✉️ Please provide a message to hide", true);
        return;
    }

    const formData = new FormData();
    formData.append("image", fileInput.files[0]);
    formData.append("message", messageInput.value);

    fetch("/hide", {
        method: "POST",
        body: formData
    })
    .then(response => {
        const extHeader = response.headers.get("X-Image-Extension") || "png";
        return response.blob().then(blob => ({ blob, ext: extHeader }));
    })
    .then(({ blob, ext }) => {
        const downloadUrl = URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `steg-image.${ext}`;
        document.body.appendChild(a);
        a.click();
        a.remove();

        const preview = document.getElementById("previewImage");
        preview.src = downloadUrl;
        preview.style.display = "block";

        showToast("✅ Message hidden successfully!");
    })
    .catch(error => {
        console.error("Error during hiding:", error);
        showToast("❌ Failed to hide the message. Try again.", true);
    });
});

// Extract hidden message
document.getElementById("extractBtn").addEventListener("click", function () {
    const fileInput = document.getElementById("extractInput");

    if (!fileInput.files.length) {
        showToast("🖼️ Please select an image to extract from", true);
        return;
    }

    const formData = new FormData();
    formData.append("image", fileInput.files[0]);

    fetch("/extract", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.result) {
            document.getElementById("extractedResult").innerText = data.result;
            showToast("✅ Message extracted successfully!");
        } else {
            showToast("❌ No hidden message found: " + (data.error || "Unknown error"), true);
        }
    })
    .catch(error => {
        console.error("Extraction error:", error);
        showToast("🚨 Error extracting hidden message.", true);
    });
});

// Decrypt extracted message
document.getElementById("decryptBtn").addEventListener("click", function () {
    const textToDecrypt = document.getElementById("textToDecrypt").value.trim();
    const keyToDecrypt = document.getElementById("keyToDecrypt").value.trim();
    const algo = document.querySelector('input[name="algo-decrypt"]:checked').value;

    if (!textToDecrypt) {
        showToast("✉️ Please paste the encrypted text", true);
        return;
    }
    if (!keyToDecrypt) {
        showToast("🛡️ Please provide the decryption key", true);
        return;
    }

    fetch("/decrypt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textToDecrypt, key: keyToDecrypt, algorithm: algo })
    })
    .then(response => response.json())
    .then(data => {
        if (data.result) {
            document.getElementById("decryptedResult").innerText = data.result;
            showToast("✅ Message decrypted successfully!");
        } else {
            showToast("❌ Decryption failed: " + (data.error || "Unknown error"), true);
        }
    })
    .catch(error => {
        console.error("Decryption error:", error);
        showToast("🚨 An error occurred during decryption.", true);
    });
});

// Handle Light/Dark Mode Toggle
document.getElementById("themeToggle").addEventListener("click", function () {
    document.body.classList.toggle("dark-mode");

    const isDark = document.body.classList.contains("dark-mode");
    if (isDark) {
        showToast("🌙 Switched to Dark Mode");
    } else {
        showToast("☀️ Switched to Light Mode");
    }
});
