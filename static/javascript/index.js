const terminalWrapper = document.getElementById("terminal-wrapper");
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


terminalWrapper.addEventListener("click", () => {
    hiddenInput.focus({ preventScroll: true });
    window.location.reload();
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
        const command = inputSpan.textContent.trim();

        userInputEcho.innerText = command;
        outputCanvas.style.display = "block";
        outputCanvas.classList.remove("hidden");
        showingOutput = true;

        handleCommand(command);

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


function handleCommand(command) {
  const output = document.getElementById("commandOutput");

  // --- GNU-ish theme: injected once ---
  if (!document.getElementById("term-theme")) {
    const style = document.createElement("style");
    style.id = "term-theme";
    style.textContent = `
      #commandOutput{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        font-size: 13.5px;
        line-height: 1.55;
        letter-spacing: .15px;
        margin-top: 10px;
        white-space: normal;
      }
      .t-out{
        border: 1px solid rgba(148,163,184,.28);
        border-radius: 14px;
        background: rgba(2,6,23,.72);
        color: #e2e8f0;
        padding: 14px 14px 12px;
        max-width: 680px;
      }
      .t-row{ display:flex; gap:10px; align-items:baseline; }
      .t-title{
        font-weight: 800;
        color: #a7f3d0;
        margin-bottom: 8px;
      }
      .t-sub{
        color: rgba(226,232,240,.85);
        margin-bottom: 10px;
      }
      .t-hr{
        height: 1px;
        background: rgba(148,163,184,.20);
        margin: 10px 0 12px;
      }
      .t-cmd{
        display: inline-flex;
        gap: 6px;
        align-items: baseline;
        font-weight: 800;
        color: #67e8f9;
      }
      .t-flag{
        font-weight: 700;
        color: #fde68a;
      }
      .t-arg{ color: #c7d2fe; font-weight: 700; }
      .t-dim{ color: rgba(226,232,240,.72); }
      .t-ok{ color: #86efac; font-weight: 700; }
      .t-err{ color: #fca5a5; font-weight: 800; }
      .t-note{
        color: rgba(226,232,240,.78);
        border-left: 3px solid rgba(34,197,94,.55);
        padding-left: 10px;
        margin-top: 12px;
      }
      .t-list{ margin: 0; padding: 0; list-style: none; }
      .t-item{
        padding: 8px 0;
        border-bottom: 1px dashed rgba(148,163,184,.18);
      }
      .t-item:last-child{ border-bottom: none; }
      .t-desc{ margin-top: 4px; color: rgba(226,232,240,.78); }
      .t-kbd{
        display:inline-block;
        padding: 1px 8px;
        border: 1px solid rgba(148,163,184,.25);
        border-radius: 999px;
        background: rgba(15,23,42,.55);
        color: #e2e8f0;
        font-weight: 700;
        font-size: 12px;
      }

      /* Light mode fallback if you ever render output outside dark cards */
      @media (prefers-color-scheme: light){
        .t-out{
          background: rgba(255,255,255,.92);
          color:#0f172a;
          border-color: rgba(148,163,184,.45);
        }
        .t-title{ color:#15803d; }
        .t-sub,.t-dim,.t-desc{ color: rgba(15,23,42,.72); }
        .t-hr{ background: rgba(148,163,184,.28); }
        .t-note{ border-left-color: rgba(16,185,129,.7); }
        .t-cmd{ color:#0891b2; }
        .t-flag{ color:#b45309; }
        .t-arg{ color:#4338ca; }
        .t-ok{ color:#15803d; }
        .t-err{ color:#b91c1c; }
        .t-kbd{ background: rgba(241,245,249,.9); color:#0f172a; }
      }
    `;
    document.head.appendChild(style);
  }

  // --- helpers ---
  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));

  const wrap = (title, subtitle, body, note = "") => `
    <div class="t-out" role="region" aria-label="terminal output">
      <div class="t-title">${esc(title)}</div>
      ${subtitle ? `<div class="t-sub">${subtitle}</div>` : ""}
      <div class="t-hr"></div>
      ${body}
      ${note ? `<div class="t-note">${note}</div>` : ""}
    </div>
  `;

  const cmd = (name, flag = "", arg = "") => `
    <span class="t-cmd">${esc(name)} ${flag ? `<span class="t-flag">${esc(flag)}</span>` : ""} ${arg ? `<span class="t-arg">${esc(arg)}</span>` : ""}</span>
  `;

  const item = (left, desc) => `
    <li class="t-item">
      <div class="t-row">${left}</div>
      ${desc ? `<div class="t-desc">${desc}</div>` : ""}
    </li>
  `;

  // --- parse command properly: base + flags + args ---
  const raw = command.trim();
  output.innerHTML = "";

  if (!raw) return;

  const tokens = raw.split(/\s+/);
  const base = tokens[0];
  const args = tokens.slice(1);

  const has = (x) => args.includes(x);
  const after = (x) => {
    const i = args.indexOf(x);
    return i >= 0 ? args[i + 1] : undefined;
  };

  switch (base) {
    case "help": {
      const body = `
        <ul class="t-list">
          ${item(cmd("help"), `Show this help screen.`)}
          ${item(cmd("menu", "--show"), `Show a quick navigation menu of your portfolio.`)}
          ${item(cmd("resume", "--download"), `Download my resume PDF.`)}
          ${item(cmd("about"), `A short summary of who I am and what I build.`)}
          ${item(cmd("projects"), `Jump to Projects section.`)}
          ${item(cmd("clear"), `Clear the terminal output.`)}
          ${item(cmd("blog"), `Open blog index.`)}
          ${item(cmd("blog", "-f", "latest"), `Open the latest blog post.`)}
        </ul>
      `;
      output.innerHTML = wrap(
        "help",
        `GNU-ish commands. Try ${`<span class="t-kbd">menu --show</span>`} or ${`<span class="t-kbd">about</span>`}.`,
        body,
        `Tip: Type <span class="t-kbd">help</span> anytime.`
      );
      break;
    }

    case "menu": {
      if (has("--show")) {
        const body = `
          <ul class="t-list">
            ${item(`<span class="t-dim">[1]</span> ${cmd("about")}`, `Who I am, what I optimize for.`)}
            ${item(`<span class="t-dim">[2]</span> ${cmd("projects")}`, `What I’ve built, shipped, and deployed.`)}
            ${item(`<span class="t-dim">[3]</span> ${cmd("stack")}`, `DevOps + Cloud + Tooling.`)}
            ${item(`<span class="t-dim">[4]</span> ${cmd("experience")}`, `Highlights and impact.`)}
            ${item(`<span class="t-dim">[5]</span> ${cmd("contact")}`, `Ways to reach me.`)}
          </ul>
        `;
        output.innerHTML = wrap("menu", "Portfolio sections", body, `Try: <span class="t-kbd">projects</span>`);
      } else {
        output.innerHTML = wrap(
          "menu",
          "",
          `<div class="t-err">Missing option.</div><div class="t-desc">Use: ${cmd("menu", "--show")}</div>`
        );
      }
      break;
    }

    case "resume": {
      if (has("--download")) {
        output.innerHTML = wrap("resume", "", `<div class="t-ok">Preparing download…</div><div class="t-desc">One moment.</div>`);
        setTimeout(() => {
          window.location.href = "/resume.pdf";
        }, 500);
      } else {
        output.innerHTML = wrap(
          "resume",
          "",
          `<div class="t-err">Unknown option.</div><div class="t-desc">Use: ${cmd("resume", "--download")}</div>`
        );
      }
      break;
    }

    case "about": {
      const body = `
        <div class="t-sub"><span class="t-cmd">DevOps / Cloud Engineer</span> with a bias for reliability, speed, and clean automation.</div>
        <ul class="t-list">
          ${item(`<span class="t-ok">•</span> CI/CD`, `Pipelines that ship safely and frequently.`)}
          ${item(`<span class="t-ok">•</span> Containers`, `Docker, orchestration, and sane environments.`)}
          ${item(`<span class="t-ok">•</span> AWS`, `Infra, networking, deployment patterns.`)}
          ${item(`<span class="t-ok">•</span> Observability`, `Logging, metrics, alerting, incident hygiene.`)}
        </ul>
      `;
      output.innerHTML = wrap("about", "", body, `Try: <span class="t-kbd">projects</span> or <span class="t-kbd">menu --show</span>`);
      break;
    }

    case "projects": {
      // If you have a section anchor, update this to match your DOM
      output.innerHTML = wrap("projects", "", `<div class="t-ok">Jumping to Projects…</div>`);
      setTimeout(() => {
        window.location.href = "/#projects";
      }, 300);
      break;
    }

    case "blog": {
      const fmt = after("-f");
      if (fmt === "latest") {
        output.innerHTML = wrap("blog", "", `<div class="t-ok">Opening latest post…</div>`);
        setTimeout(() => {
          window.location.href = "/blog?b=" + Date.now();
        }, 450);
      } else {
        output.innerHTML = wrap("blog", "", `<div class="t-ok">Opening blog index…</div>`);
        setTimeout(() => {
          window.location.href = "/blog";
        }, 450);
      }
      break;
    }

    case "clear": {
      // keep your existing behavior
      outputCanvas.style.display = "none";
      output.innerHTML = "";
      userInputEcho.innerText = "";
      showingOutput = false;
      break;
    }

    case "": {
      output.innerHTML = "";
      break;
    }

    default: {
      output.innerHTML = wrap(
        "error",
        "",
        `<div class="t-err">command not found:</div>
         <div class="t-desc"><span class="t-kbd">${esc(raw)}</span></div>`,
        `Type <span class="t-kbd">help</span> to see available commands.`
      );
      break;
    }
  }
}


updateCursor();
hiddenInput.focus({ preventScroll: true });
lucide.createIcons();