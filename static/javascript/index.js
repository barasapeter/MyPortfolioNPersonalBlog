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
        console.log("command:", inputSpan.textContent);
        userInputEcho.innerText = inputSpan.textContent;
        outputCanvas.style.display = "block";
        showingOutput = true;

        inputSpan.textContent = "";
        updateCursor();
        e.preventDefault();
        return;
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