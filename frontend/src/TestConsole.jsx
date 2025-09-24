import { useState } from "react";

export default function TestConsole(){
  const [tab, setTab] = useState("telegram");
  const [telegram, setTelegram] = useState({ channel:"@durov", keywords:"telegram" });
  const [output, setOutput] = useState("");

  const call = async (url, body) => {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type":"application/json" },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    setOutput(JSON.stringify(data, null, 2));
  };

  return (
    <div style={{maxWidth:800, margin:"40px auto", fontFamily:"system-ui"}}>
      <h2>Test Console</h2>
      <div style={{display:"flex", gap:12, marginBottom:12}}>
        <button onClick={()=>setTab("telegram")}>Telegram Scan</button>
        <button onClick={()=>setTab("help")}>Help</button>
      </div>

      {tab==="telegram" && (
        <div style={{display:"grid", gap:12}}>
          <label>Channel (e.g. @somepublicchannel)
            <input value={telegram.channel} onChange={e=>setTelegram(v=>({...v,channel:e.target.value}))} />
          </label>
          <label>Keywords (comma separated)
            <input value={telegram.keywords} onChange={e=>setTelegram(v=>({...v,keywords:e.target.value}))} />
          </label>
          <button onClick={()=>call("/api/scan/telegram/manual/", {
            channel: telegram.channel.trim(),
            keywords: telegram.keywords.split(",").map(s=>s.trim()).filter(Boolean)
          })}>Run Telegram Manual Scan</button>
        </div>
      )}

      {tab==="help" && (
        <ul>
          <li>Telegram Bot Webhook: add the bot to a chat and hit /webhooks/telegram/&lt;secret&gt;/</li>
          <li>WhatsApp Cloud: set webhook URL in Meta dev console to /webhooks/whatsapp/ (GET verify + POST receive)</li>
          <li>Results appear in /admin/ → Scanned content</li>
        </ul>
      )}

      <pre style={{marginTop:20, background:"#f7f7f7", padding:12, borderRadius:8, minHeight:120}}>{output}</pre>
    </div>
  );
}
