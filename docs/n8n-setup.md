# n8n setup (about 5 minutes)

1. Start n8n with `npx n8n` (Safari: `N8N_SECURE_COOKIE=false npx n8n`), open http://localhost:5678, create the local owner account.
2. Credentials → Add → **Header Auth**: Name `X-API-Key`, Value = the `API_KEY` from your `.env`.
3. Credentials → Add → **SMTP**: your Gmail address, a Gmail app password, host `smtp.gmail.com`, port 465, SSL on.
4. ⋯ menu → **Import from file** → `n8n/risk-alerts.json`, then `n8n/daily-briefing.json`.
5. In each imported workflow, open every HTTP Request node and select the Header Auth credential; open every Send Email node, select the SMTP credential, and replace the placeholder addresses (`*@directorate.example`) with yours. Keep `127.0.0.1`, not `localhost`, in URLs (Node resolves `localhost` to IPv6; the API listens on IPv4).
6. ⋯ menu → Settings → Timezone `Asia/Riyadh` on both workflows.
7. Open **Daily briefing** → Execute workflow. The draft arrives by email in 1–3 minutes; open the form link on the same machine, approve, and the formatted briefing arrives at the DG address. Run it again and reject, to see the other branch.
8. Open **Risk alerts** → Execute workflow. Pending high-risk items arrive as one email; a second run sends nothing.

Publish each workflow only when you want the schedules live.
