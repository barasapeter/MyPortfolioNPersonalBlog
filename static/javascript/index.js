const terminal = document.getElementById("terminal");
const hiddenInput = document.getElementById("hiddenInput");
const inputSpan = document.getElementById("input");
const placeholder = document.getElementById("placeholder");
const inputContainer = document.getElementById("input-container");
const cursor = document.querySelector(".cursor");
const outputCanvas = document.getElementById("outputCanvas");
const userInputEcho = document.getElementById("userInputEcho");

let showingOutput = false;


function updateCursor() {
    inputContainer.insertBefore(cursor, inputSpan.nextSibling);
    updatePlaceholder();
}

function updatePlaceholder() {
    placeholder.style.display =
        inputSpan.textContent.length === 0 ? "inline" : "none";
}

terminal.addEventListener("mousedown", () => {
    hiddenInput.focus();
});

hiddenInput.addEventListener("blur", () => {
    setTimeout(() => hiddenInput.focus(), 0);
});

function handleCommand(command) {
    const output = document.getElementById("commandOutput");

    // Helper to wrap text in color
    const color = (text, type) => {
        switch (type) {
            case "keyword": return `<span class="text-cyan-400 font-bold">${text}</span>`;
            case "flag": return `<span class="text-yellow-400">${text}</span>`;
            case "note": return `<span class="text-green-400 italic">${text}</span>`;
            case "error": return `<span class="text-red-400">${text}</span>`;
            default: return text;
        }
    };

    // Split command + flags
    const [base, flag] = command.split(" ");

    // Enable HTML in output
    output.innerHTML = "";

    switch (base) {
        case "help":
            output.innerHTML = `
${color("Available commands:", "note")}

• ${color("help", "keyword")}
  Show this help menu

• ${color("menu", "keyword")} ${color("--show", "flag")}
  Display summarized portfolio sections

• ${color("resume", "keyword")} ${color("--download", "flag")}
  Download my resume

• ${color("about", "keyword")}
  Who am I? - summarized

• ${color("clear", "keyword")}
  Clear the terminal

• ${color("blog", "keyword")}
  View my Blogs. Problems and how I solved them

• ${color("blog -f latest", "keyword")}
  Get the latest blog

${color("Type a command and press Enter.", "note")}
`;
            break;

        case "menu":
            if (flag === "--show") {
                output.innerHTML = `
${color("Portfolio Menu:", "note")}

[1] ${color("About Me", "keyword")}
[2] ${color("Projects", "keyword")}
[3] ${color("DevOps Stack", "keyword")}
[4] ${color("Experience", "keyword")}
[5] ${color("Contact", "keyword")}

${color('Tip: Try "about" or "projects"', "note")}
`;
            } else {
                output.innerHTML = color(`Unknown option for menu. Try: menu --show`, "error");
            }
            break;

        case "resume":
            if (flag === "--download") {
                output.innerHTML = color("Downloading resume...", "note");

                setTimeout(() => {
                    window.location.href = "/resume.pdf";
                }, 800);
            } else {
                output.innerHTML = color(`Unknown option for resume. Try: resume --download`, "error");
            }
            break;

        case "about":
            output.innerHTML = `
${color("DevOps Engineer", "keyword")}

• ${color("CI/CD pipelines", "note")}
• ${color("Docker & Kubernetes", "note")}
• ${color("AWS / Cloud Infrastructure", "note")}
• ${color("Automation & Monitoring", "note")}

${color("Building reliable systems.", "note")}
`;
            break;

        case "clear":
            outputCanvas.style.display = "none";
            output.innerHTML = "";
            userInputEcho.innerText = "";
            showingOutput = false;
            break;

        case "blog":
            output.innerHTML = `${color("Opening Blogs...", "note")}`;
            setTimeout(() => {
                window.location.href = "/blog";
            }, 800);


        case "blog -f latest":
            output.innerHTML = `${color("Opening latest blog...", "note")}`;
            setTimeout(() => {
                window.location.href = "/blog?b=" + new Date();
            }, 800);



        case "":
            output.innerHTML = "";
            break;

        default:
            output.innerHTML = `
${color(`Command not found: ${command}`, "error")}

${color('Type "help" to see available commands.', "note")}
`;
    }
}



hiddenInput.addEventListener("keydown", (e) => {

    if (showingOutput && e.key.length === 1) {
        outputCanvas.style.display = "none";
        showingOutput = false;
    }

    if (e.key === "Backspace") {
        inputSpan.textContent = inputSpan.textContent.slice(0, -1);
        updateCursor();
        e.preventDefault();
        return;
    }

    if (e.key === "Enter") {
        const command = inputSpan.textContent.trim();

        userInputEcho.innerText = command;
        outputCanvas.style.display = "block";
        outputCanvas.classList.remove("hidden");
        showingOutput = true;

        handleCommand(command);

        inputSpan.textContent = "";
        updateCursor();
        e.preventDefault();
    }


    if (e.key.length === 1) {
        inputSpan.textContent += e.key;
        updateCursor();
        e.preventDefault();
    }
});

updateCursor();
hiddenInput.focus();
lucide.createIcons();