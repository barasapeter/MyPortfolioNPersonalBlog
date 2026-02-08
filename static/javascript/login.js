document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const button = document.getElementById("loginBtn");
    const errorBanner = document.getElementById("errorBanner");

    if (!form || !button || !errorBanner) {
        console.error("Login form elements not found");
        return;
    }

    function setLoading(isLoading) {
        button.disabled = isLoading;
        button.textContent = isLoading ? "Signing in…" : "Next";
    }

    function showError(message) {
        errorBanner.textContent = message;
        errorBanner.classList.remove("hidden");
    }

    function clearError() {
        errorBanner.classList.add("hidden");
        errorBanner.textContent = "";
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        clearError();

        const identifier = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value;

        if (!identifier || !password) {
            showError("Please enter both username/email and password.");
            return;
        }

        const payload = {
            password,
            ...(identifier.includes("@")
                ? { email: identifier }
                : { username: identifier }),
        };

        setLoading(true);

        try {
            const res = await fetch("/api/v1/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: "include",
                body: JSON.stringify(payload),
            });

            const data = await res.json();

            if (!res.ok) {
                showError(data.detail || "Invalid credentials.");
                setLoading(false);
                return;
            }

            window.location.href = data.redirect || "/blog";
        } catch (err) {
            console.error(err);
            showError("Network error. Please try again.");
            setLoading(false);
        } finally {
            setLoading(false);
        }
    });
});
