document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("summarizeBtn");
    const inputText = document.getElementById("inputText");
    const output = document.getElementById("output");
    const status = document.getElementById("status");

    btn.addEventListener("click", async () => {
        const text = inputText.value.trim();

        if (!text) {
            alert("Please enter text to summarize");
            return;
        }

        btn.disabled = true;
        status.textContent = "Summarizing... please wait";
        output.textContent = "";

        try {
            const formData = new FormData();
            formData.append("text", text);

            const response = await fetch("/summarize", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (data.summary) {
                output.textContent = data.summary;
                status.textContent = "";
            } else {
                status.textContent = data.error || "Unknown error";
            }

        } catch (err) {
            console.error(err);
            status.textContent = "Server error. Check console.";
        }

        btn.disabled = false;
    });
});
