// 后端 FastAPI 服务地址（如果前后端同域可改为 ""）
const API_BASE = "http://127.0.0.1:1002";

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function loadConfig() {
  try {
    const res = await fetch(`${API_BASE}/api/config`);
    if (!res.ok) return;
    const cfg = await res.json();
    document.getElementById("base_url").value = cfg.external_api_base_url || "";
    document.getElementById("api_key").value = cfg.external_api_key || "";
    document.getElementById("current_api_key").value = cfg.api_key || "";
  } catch (e) {
    console.error("Failed to load config", e);
  }
}

async function saveConfig(e) {
  e.preventDefault();
  const status = document.getElementById("config-status");
  status.textContent = "Saving...";
  try {
    const body = {
      external_api_base_url: document.getElementById("base_url").value,
      external_api_key: document.getElementById("api_key").value,
    };
    const res = await fetch(`${API_BASE}/api/config`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      status.textContent = "Failed to save";
      return;
    }
    status.textContent = "Saved";
    setTimeout(() => (status.textContent = ""), 2000);
  } catch (e) {
    console.error("Failed to save config", e);
    status.textContent = "Error";
  }
}

async function loadLogs() {
  try {
    const res = await fetch(`${API_BASE}/api/logs`);
    if (!res.ok) return;
    const logs = await res.json();
    const container = document.getElementById("logs");
    container.innerHTML = "";
    logs.slice(0, 10).forEach((log) => {
      const entry = document.createElement("div");
      entry.className = "log-entry";
      const prompt = escapeHtml(log.prompt || "");

      let prettyRequest = "";
      try {
        prettyRequest = JSON.stringify(
          JSON.parse(log.request_body || "{}"),
          null,
          2
        );
      } catch {
        prettyRequest = log.request_body || "";
      }

      let prettyResponse = "";
      let streamContent = "";
      let streamChunks = null;
      try {
        const parsed = JSON.parse(log.response || "{}");
        prettyResponse = JSON.stringify(parsed, null, 2);
        if (parsed && parsed.stream === true) {
          streamContent =
            typeof parsed.content === "string" ? parsed.content : String(parsed.content ?? "");
          if (Array.isArray(parsed.chunks)) {
            streamChunks = parsed.chunks;
          }
        }
      } catch {
        prettyResponse = log.response || "";
      }

      entry.innerHTML = `
        <div class="log-header">Timestamp: ${log.timestamp}</div>
        <div class="log-content"><strong>Prompt (summary):</strong> ${prompt}</div>
        <div class="log-content"><strong>Request JSON:</strong></div>
        <pre class="log-json">${escapeHtml(prettyRequest)}</pre>
        ${
          streamChunks
            ? `<div class="log-content"><strong>Stream content (assembled):</strong></div>
               <pre class="log-json">${escapeHtml(streamContent)}</pre>
               <div class="log-content"><strong>Stream chunks (each SSE data JSON):</strong></div>
               <div class="log-chunks-wrapper">
                 ${streamChunks
                   .map((chunk, idx) => {
                     const label =
                       chunk && chunk.event === "[DONE]" ? "DONE" : "Chunk #" + (idx + 1);
                     return (
                       '<div class="log-content"><strong>' +
                       label +
                       ':</strong></div>' +
                       '<pre class="log-json">' +
                       escapeHtml(JSON.stringify(chunk, null, 2)) +
                       "</pre>"
                     );
                   })
                   .join("")}
               </div>`
            : `<div class="log-content"><strong>Response JSON:</strong></div>
               <pre class="log-json">${escapeHtml(prettyResponse)}</pre>`
        }
        <div class="log-meta">
          Tokens: ${log.tokens_used ?? "N/A"} | API: ${log.external_api_url}
        </div>
      `;
      container.appendChild(entry);
    });
  } catch (e) {
    console.error("Failed to load logs", e);
  }
}

async function generateApiKey() {
  const status = document.getElementById("api-key-status");
  status.textContent = "Generating...";
  try {
    const res = await fetch(`${API_BASE}/api/generate-api-key`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) {
      status.textContent = "Failed to generate";
      return;
    }
    const data = await res.json();
    document.getElementById("current_api_key").value = data.api_key;
    status.textContent = "Generated";
    setTimeout(() => (status.textContent = ""), 2000);
  } catch (e) {
    console.error("Failed to generate API key", e);
    status.textContent = "Error";
  }
}

async function sendChat() {
  const promptEl = document.getElementById("prompt");
  const prompt = promptEl.value;
  if (!prompt.trim()) return;

  const chatMessages = document.getElementById("chat-messages");
  const escapedPrompt = escapeHtml(prompt);
  const userMessage = document.createElement("div");
  userMessage.className = "chat-message user-message";
  userMessage.innerHTML = `<strong>You:</strong> ${escapedPrompt}`;
  chatMessages.appendChild(userMessage);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  document.getElementById("loading").style.display = "block";

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        prompt, 
        model: document.getElementById("web_model").value 
      }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let assistantMessage = "";
    let messageElement = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.substring(6);
          if (data === "[DONE]") {
            document.getElementById("loading").style.display = "none";
            break;
          }

          try {
            const jsonData = JSON.parse(data);
            if (jsonData.error) {
              const errorDiv = document.createElement("div");
              errorDiv.className = "chat-message assistant-message";
              errorDiv.innerHTML = `<strong>Error:</strong> ${escapeHtml(
                jsonData.error.toString()
              )}`;
              chatMessages.appendChild(errorDiv);
              document.getElementById("loading").style.display = "none";
              return;
            }

            if (jsonData.choices && jsonData.choices.length > 0) {
              const delta = jsonData.choices[0].delta || {};
              if (delta.content) {
                assistantMessage += delta.content;
                if (!messageElement) {
                  const wrapper = document.createElement("div");
                  wrapper.className = "chat-message assistant-message";
                  wrapper.innerHTML =
                    '<strong>Assistant:</strong> <span id="assistant-content"></span>';
                  chatMessages.appendChild(wrapper);
                  messageElement = wrapper.querySelector("#assistant-content");
                }
                messageElement.textContent = assistantMessage;
                chatMessages.scrollTop = chatMessages.scrollHeight;
              }
            }
          } catch (e) {
            console.error("Error parsing chunk", e);
          }
        }
      }
    }

    promptEl.value = "";
    document.getElementById("loading").style.display = "none";
    await loadLogs();
  } catch (error) {
    console.error("Error sending request:", error);
    document.getElementById("loading").style.display = "none";
    const errorDiv = document.createElement("div");
    errorDiv.className = "chat-message assistant-message";
    errorDiv.innerHTML = `<strong>Error:</strong> ${escapeHtml(error.message)}`;
    chatMessages.appendChild(errorDiv);
  }
}

let autoRefreshLogs = true;

document.addEventListener("DOMContentLoaded", () => {
  loadConfig();
  loadLogs();

  const logsContainer = document.getElementById("logs");
  if (logsContainer) {
    // 鼠标移入日志区域时，暂停自动刷新，避免滚动被打断
    logsContainer.addEventListener("mouseenter", () => {
      autoRefreshLogs = false;
    });
    // 鼠标移出后，恢复自动刷新
    logsContainer.addEventListener("mouseleave", () => {
      autoRefreshLogs = true;
    });
  }

  // 定时刷新日志，实现“实时”效果（仅在未查看日志时刷新）
  setInterval(() => {
    if (autoRefreshLogs) {
      loadLogs();
    }
  }, 2000);

  document
    .getElementById("config-form")
    .addEventListener("submit", saveConfig);
  document.getElementById("send-btn").addEventListener("click", sendChat);
  document.getElementById("generate-api-key-btn").addEventListener("click", generateApiKey);
});

