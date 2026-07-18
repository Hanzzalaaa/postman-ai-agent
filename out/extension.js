"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
const os = __importStar(require("os"));
const fs = __importStar(require("fs"));
// ─── Get env path ─────────────────────────────────────────────────────────────
function getEnvPath() {
    return path.join(os.homedir(), ".postman-agent", ".env");
}
// ─── Check if setup done ──────────────────────────────────────────────────────
function isSetupDone() {
    const envPath = getEnvPath();
    return fs.existsSync(envPath);
}
// ─── Save API keys ────────────────────────────────────────────────────────────
function saveApiKeys(groqKey, postmanKey) {
    const envDir = path.join(os.homedir(), ".postman-agent");
    if (!fs.existsSync(envDir)) {
        fs.mkdirSync(envDir, { recursive: true });
    }
    fs.writeFileSync(getEnvPath(), `GROQ_API_KEY=${groqKey}\nPOSTMAN_API_KEY=${postmanKey}\n`);
}
// ─── Create Webview Panel ─────────────────────────────────────────────────────
function createChatPanel(context) {
    const panel = vscode.window.createWebviewPanel("postmanAiAgent", "🤖 Postman AI Agent", vscode.ViewColumn.Two, {
        enableScripts: true,
        retainContextWhenHidden: true,
    });
    panel.webview.html = getChatHTML();
    return panel;
}
// ─── Chat HTML ────────────────────────────────────────────────────────────────
function getChatHTML() {
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Postman AI Agent</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #0d1117;
      color: #e6edf3;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* ─── Header ─── */
    .header {
      background: linear-gradient(135deg, #6e40c9, #2563eb);
      padding: 16px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .header-icon {
      width: 40px;
      height: 40px;
      background: rgba(255,255,255,0.2);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
    }

    .header-text h1 {
      font-size: 16px;
      font-weight: 700;
      color: white;
    }

    .header-text p {
      font-size: 11px;
      color: rgba(255,255,255,0.7);
    }

    .status-dot {
      width: 8px;
      height: 8px;
      background: #22c55e;
      border-radius: 50%;
      margin-left: auto;
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    /* ─── Messages ─── */
    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .message {
      display: flex;
      gap: 10px;
      animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .message-avatar {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      flex-shrink: 0;
    }

    .bot-avatar { background: linear-gradient(135deg, #6e40c9, #2563eb); }
    .user-avatar { background: #21262d; }

    .message-content {
      flex: 1;
    }

    .message-label {
      font-size: 11px;
      color: #7d8590;
      margin-bottom: 4px;
    }

    .message-bubble {
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 12px;
      padding: 12px 16px;
      font-size: 13px;
      line-height: 1.6;
    }

    .user-bubble {
      background: #1c2128;
      border-color: #6e40c9;
    }

    /* ─── Input Form ─── */
    .input-form {
      padding: 16px 20px;
      background: #161b22;
      border-top: 1px solid #30363d;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .input-row {
      display: flex;
      gap: 10px;
    }

    input[type="text"],
    input[type="password"] {
      flex: 1;
      background: #0d1117;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 10px 14px;
      color: #e6edf3;
      font-size: 13px;
      outline: none;
      transition: border-color 0.2s;
    }

    input:focus {
      border-color: #6e40c9;
    }

    input::placeholder { color: #7d8590; }

    button {
      background: linear-gradient(135deg, #6e40c9, #2563eb);
      color: white;
      border: none;
      border-radius: 8px;
      padding: 10px 18px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.2s;
      white-space: nowrap;
    }

    button:hover { opacity: 0.9; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }

    /* ─── Route Tags ─── */
    .route-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #21262d;
      border: 1px solid #30363d;
      border-radius: 6px;
      padding: 4px 8px;
      margin: 3px;
      font-size: 11px;
      font-family: monospace;
    }

    .method-badge {
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 700;
      font-size: 10px;
    }

    .GET { background: #1d4ed8; color: #93c5fd; }
    .POST { background: #15803d; color: #86efac; }
    .PUT { background: #b45309; color: #fcd34d; }
    .DELETE { background: #dc2626; color: #fca5a5; }
    .PATCH { background: #7c3aed; color: #c4b5fd; }

    /* ─── Open Button ─── */
    .open-btn {
      background: linear-gradient(135deg, #15803d, #16a34a);
      width: 100%;
      margin-top: 8px;
      padding: 12px;
      font-size: 14px;
    }

    /* ─── Loading ─── */
    .loading {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #7d8590;
      font-size: 12px;
    }

    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid #30363d;
      border-top-color: #6e40c9;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .routes-container {
      display: flex;
      flex-wrap: wrap;
      margin-top: 8px;
    }
  </style>
</head>
<body>

  <!-- Header -->
  <div class="header">
    <div class="header-icon">🤖</div>
    <div class="header-text">
      <h1>Postman AI Agent</h1>
      <p>LangGraph + Groq + Postman API</p>
    </div>
    <div class="status-dot"></div>
  </div>

  <!-- Messages -->
  <div class="messages" id="messages">
    <div class="message">
      <div class="message-avatar bot-avatar">🤖</div>
      <div class="message-content">
        <div class="message-label">Postman AI Agent</div>
        <div class="message-bubble">
            Hello! I'm your Postman AI Agent.<br><br>
          I can automatically analyze your backend code and generate Postman Collections!<br><br>
          To get started, I need your API keys. Don't worry — they're stored securely on your machine only.
        </div>
      </div>
    </div>
  </div>

  <!-- Input -->
  <div class="input-form" id="setupForm">
    <div class="input-row">
      <input type="password" id="groqKey" placeholder="Enter GROQ API Key (free at console.groq.com)" />
    </div>
    <div class="input-row">
      <input type="password" id="postmanKey" placeholder="Enter Postman API Key (free at postman.com)" />
    </div>
    <div class="input-row">
      <button onclick="saveKeys()">Save Keys & Start</button>
    </div>
  </div>

  <div class="input-form" id="updateForm" style="display:none;">
    <div class="input-row">
      <button onclick="showUpdateKeys()" style="background: #21262d; border: 1px solid #6e40c9;">
        Update API Keys
      </button>
      <button onclick="deleteKeys()" style="background: #21262d; border: 1px solid #dc2626; color: #fca5a5;">
        Delete Keys
      </button>
    </div>
  </div>

  <div class="input-form" id="scanForm" style="display:none;">
    <div class="input-row">
      <button onclick="scanProject()" id="scanBtn">Generate Postman Collection</button>
    </div>
  </div>

  <script>
    const vscode = acquireVsCodeApi();
    let postmanUrl = '';

    function showUpdateKeys() {
      document.getElementById('updateForm').style.display = 'none';
      document.getElementById('setupForm').style.display = 'flex';
      document.getElementById('groqKey').value = '';
      document.getElementById('postmanKey').value = '';
      addMessage('bot', 'Enter your new API keys below:');
    }

    function deleteKeys() {
      vscode.postMessage({ command: 'deleteKeys' });
    }

    // ─── Save Keys ──────────────────────────────────────────────────────────
    function saveKeys() {
      const groqKey = document.getElementById('groqKey').value.trim();
      const postmanKey = document.getElementById('postmanKey').value.trim();

      if (!groqKey || !postmanKey) {
        addMessage('bot', 'Please enter both API keys!');
        return;
      }

      addMessage('user', 'API Keys entered');
      addMessage('bot', 'Saving your API keys securely...');

      vscode.postMessage({ command: 'saveKeys', groqKey, postmanKey });
    }

    // ─── Scan Project ────────────────────────────────────────────────────────
    function scanProject() {
      const btn = document.getElementById('scanBtn');
      btn.disabled = true;
      btn.textContent = 'Analyzing...';

      addMessage('user', 'Generate Postman Collection for this project');
      addMessage('bot', '<div class="loading"><div class="spinner"></div> AI Agent analyzing your code... Please wait!</div>');

      vscode.postMessage({ command: 'scanProject' });
    }

    // ─── Open Postman ────────────────────────────────────────────────────────
    function openPostman() {
      vscode.postMessage({ command: 'openUrl', url: postmanUrl });
    }

    // ─── Add Message ─────────────────────────────────────────────────────────
    function addMessage(type, content) {
      const messages = document.getElementById('messages');
      const div = document.createElement('div');
      div.className = 'message';
      div.innerHTML = \`
        <div class="message-avatar \${type === 'bot' ? 'bot-avatar' : 'user-avatar'}">\${type === 'bot' ? '🤖' : '👤'}</div>
        <div class="message-content">
          <div class="message-label">\${type === 'bot' ? 'Postman AI Agent' : 'You'}</div>
          <div class="message-bubble \${type === 'user' ? 'user-bubble' : ''}">\${content}</div>
        </div>
      \`;
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }

    // ─── Handle Messages from Extension ──────────────────────────────────────
    window.addEventListener('message', event => {
      const msg = event.data;

      if (msg.command === 'keysSaved') {
        addMessage('bot', 'API keys saved successfully!<br><br>Now I can analyze your project. Click the button below to generate your Postman Collection!');
        document.getElementById('setupForm').style.display = 'none';
        document.getElementById('scanForm').style.display = 'flex';
      }

      if (msg.command === 'alreadySetup') {
        addMessage('bot', 'API keys already configured! You can generate a collection or manage your keys.');
        document.getElementById('setupForm').style.display = 'none';
        document.getElementById('updateForm').style.display = 'flex';
        document.getElementById('scanForm').style.display = 'flex';
      }

      if (msg.command === 'keysDeleted') {
        addMessage('bot', 'Keys deleted! Please enter new API keys.');
        document.getElementById('updateForm').style.display = 'none';
        document.getElementById('scanForm').style.display = 'none';
        document.getElementById('setupForm').style.display = 'flex';
      }

      if (msg.command === 'scanResult') {
        const btn = document.getElementById('scanBtn');
        btn.disabled = false;
        btn.textContent = 'Generate Postman Collection';

        if (msg.success) {
          postmanUrl = msg.postmanUrl;

          let routesHtml = '<div class="routes-container">';
          msg.routes.forEach(r => {
            routesHtml += \`<div class="route-tag"><span class="method-badge \${r.method}">\${r.method}</span>\${r.path}</div>\`;
          });
          routesHtml += '</div>';

          addMessage('bot', \`
            🎉 <strong>Success! Found \${msg.routeCount} routes!</strong><br><br>
            \${routesHtml}
            <br>
            <button class="open-btn" onclick="openPostman()">🔗 Open in Postman</button>
          \`);
        } else {
          addMessage('bot', \` Error: \${msg.error}<br><br>Make sure postman-agent is installed:<br><code>pip install postman-agent</code>\`);
        }
      }
    });
  </script>
</body>
</html>`;
}
function activate(context) {
    let panel;
    // ─── Open Chat Panel ───────────────────────────────────────────────────────
    const openPanel = (projectPath) => {
        if (panel) {
            panel.reveal(vscode.ViewColumn.Two);
        }
        else {
            panel = createChatPanel(context);
            panel.onDidDispose(() => { panel = undefined; });
        }
        // ─── Handle messages from webview ───────────────────────────────────
        panel.webview.onDidReceiveMessage(async (msg) => {
            if (msg.command === 'checkSetup') {
                if (isSetupDone()) {
                    panel?.webview.postMessage({ command: 'alreadySetup' });
                }
                else {
                    panel?.webview.postMessage({ command: 'needSetup' });
                }
            }
            if (msg.command === 'saveKeys') {
                saveApiKeys(msg.groqKey, msg.postmanKey);
                panel?.webview.postMessage({ command: 'keysSaved' });
            }
            if (msg.command === 'openUrl') {
                vscode.env.openExternal(vscode.Uri.parse(msg.url));
            }
            if (msg.command === 'deleteKeys') {
                const envPath = path.join(os.homedir(), '.postman-agent', '.env');
                if (fs.existsSync(envPath)) {
                    fs.unlinkSync(envPath);
                }
                panel?.webview.postMessage({ command: 'keysDeleted' });
            }
            if (msg.command === 'scanProject') {
                const workspaceFolders = vscode.workspace.workspaceFolders;
                const scanPath = projectPath || workspaceFolders?.[0]?.uri.fsPath;
                if (!scanPath) {
                    panel?.webview.postMessage({
                        command: 'scanResult',
                        success: false,
                        error: 'No project folder open!'
                    });
                    return;
                }
                (0, child_process_1.exec)(`cmd /c postman-agent generate --scan "${scanPath}"`, { timeout: 120000, shell: 'cmd.exe' }, (error, stdout, stderr) => {
                    if (error) {
                        panel?.webview.postMessage({
                            command: 'scanResult',
                            success: false,
                            error: error.message
                        });
                        return;
                    }
                    // ─── Parse output ──────────────────────────────────────────
                    const lines = stdout.split('\n');
                    let postmanUrl = '';
                    let routeCount = 0;
                    const routes = [];
                    for (const line of lines) {
                        if (line.includes('go.postman.co/collection')) {
                            postmanUrl = line.replace('🔗 Open here:', '').trim();
                        }
                        if (line.includes('Found') && line.includes('routes')) {
                            const match = line.match(/(\d+) routes/);
                            if (match) {
                                routeCount = parseInt(match[1]);
                            }
                        }
                        const routeMatch = line.match(/\s+(GET|POST|PUT|DELETE|PATCH)\s+(\/\S*)/);
                        if (routeMatch) {
                            routes.push({ method: routeMatch[1], path: routeMatch[2] });
                        }
                    }
                    panel?.webview.postMessage({
                        command: 'scanResult',
                        success: true,
                        postmanUrl,
                        routeCount,
                        routes
                    });
                });
            }
        });
    };
    // ─── Commands ──────────────────────────────────────────────────────────────
    const scanProject = vscode.commands.registerCommand('postman-ai-agent.scanProject', () => openPanel());
    const scanFile = vscode.commands.registerCommand('postman-ai-agent.scanFile', (uri) => {
        const filePath = uri?.fsPath || vscode.window.activeTextEditor?.document.uri.fsPath;
        if (filePath) {
            openPanel(path.dirname(filePath));
        }
    });
    const setupKeys = vscode.commands.registerCommand('postman-ai-agent.setup', () => openPanel());
    context.subscriptions.push(scanProject, scanFile, setupKeys);
}
function deactivate() { }
//# sourceMappingURL=extension.js.map