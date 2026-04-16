# 🦞 Lobster — Adapter for Shrimpy → OpenClaw

Lobster is a **secure adapter layer** between:

* 🦐 **Shrimpy** (Nginx reverse proxy, public)
* 🧠 **Goliath** (OpenClaw Gateway, private)
* ⚡ **Orin** (optional edge compute)

---

## 🧠 Architecture

```
Internet
   |
   v
🦐 Shrimpy (Nginx :443)
   |
   v
Public chatbot app (:3000)
   |
   v
🦞 Lobster (:4000, localhost only)
   |
   v
🧠 OpenClaw (127.0.0.1:18789)
```

---

## 🔥 Core Principles

* ❌ OpenClaw is NEVER exposed publicly
* ✅ Lobster is the ONLY service allowed to talk to OpenClaw
* 🔐 Shrimpy authenticates with Lobster via shared secret
* 🛡 Lobster enforces public safety rules

---

## 🚀 Features

* Public/private mode separation
* Request sanitization
* Model allowlist
* Rate limiting (extensible)
* Streaming support (SSE-ready)
* Ready for Orin routing

---

## ⚙️ Setup

### 1. Clone repo

```bash
git clone https://github.com/<your-username>/lobster.git
cd lobster
```

---

### 2. Setup environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### 3. Configure environment

```bash
cp .env.example .env
nano .env
```

---

### 4. Run locally

```bash
./run.sh
```

---

## 🔐 Environment Variables

```env
OPENCLAW_URL=http://127.0.0.1:18789
OPENCLAW_TOKEN=your-secret-token
PUBLIC_SHARED_SECRET=your-shrimpy-secret
```

---

## 🧪 Test

```bash
curl http://127.0.0.1:4000/healthz
```

---

## 🛡 Security Model

### Public Mode

* ❌ No shell
* ❌ No filesystem writes
* ❌ No browser automation
* ✅ Restricted models only

### Private Mode

* Full capabilities (via Tailscale/admin)

---

## 🔀 Future Extensions

* Route requests to ⚡ Orin
* Add Redis rate limiting
* Add user authentication
* Add logging + analytics
* Multi-model routing

---

## 💡 Philosophy

> Shrimpy handles traffic
> Lobster handles trust
> Goliath handles intelligence

---

## 📄 License

MIT
