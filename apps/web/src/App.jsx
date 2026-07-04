import { useEffect, useMemo, useRef, useState } from "react";

/* ── constants ─────────────────────────────────── */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8081";
const AUTH_KEY = "mykb.auth";
const EMPTY_AUTH = { username: "", identity: "", password: "" };

/* ── helpers ────────────────────────────────────── */
function readAuth() {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
function writeAuth(a) {
  a ? localStorage.setItem(AUTH_KEY, JSON.stringify(a)) : localStorage.removeItem(AUTH_KEY);
}
function parseJson(t) {
  try { return JSON.parse(t); } catch { return null; }
}
function errMsg(text, payload) {
  return payload?.message ?? payload?.code ?? text?.trim() ?? "请求失败";
}
function fmtDate(v) {
  if (!v) return "";
  return new Date(v).toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" });
}
function fmtTime(v) {
  if (!v) return "";
  return new Date(v).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}
function fmtBytes(s) {
  if (!Number.isFinite(s) || s <= 0) return "0 B";
  const u = ["B", "KB", "MB", "GB"];
  let v = s, i = 0;
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(v >= 10 || i === 0 ? 0 : 1)} ${u[i]}`;
}
function tone(c) {
  return c === "success" ? "text-green-700 bg-green-50 border-green-200" : c === "danger" ? "text-red-700 bg-red-50 border-red-200" : "text-slate-600 bg-white border-outline-variant/40";
}

async function api(path, { token, formData, ...opts } = {}) {
  const h = new Headers(opts.headers ?? {});
  if (!formData) h.set("Content-Type", "application/json");
  if (token) h.set("Authorization", `Bearer ${token}`);
  const r = await fetch(`${API_BASE_URL}${path}`, { ...opts, headers: h, body: formData ?? opts.body });
  const txt = await r.text();
  const p = parseJson(txt);
  if (!r.ok) throw new Error(errMsg(txt, p));
  return p;
}

/* ── Login ──────────────────────────────────────── */
function LoginView({ status, setStatus }) {
  const [mode, setMode] = useState("login");
  const [f, setF] = useState(EMPTY_AUTH);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const path = mode === "register" ? "/api/v1/auth/register" : "/api/v1/auth/login";
      const body = mode === "register"
        ? { username: f.username.trim(), email: f.identity.trim(), password: f.password }
        : { identity: f.identity.trim(), password: f.password };
      const r = await api(path, { method: "POST", body: JSON.stringify(body) });
      const next = { token: r.data.accessToken, user: r.data.user };
      writeAuth(next);
      setF(EMPTY_AUTH);
      setStatus({ t: "success", msg: mode === "register" ? "注册成功，请登录" : "登录成功" });
      window.location.reload();
    } catch (err) {
      setStatus({ t: "danger", msg: `${mode === "register" ? "注册" : "登录"}失败: ${err.message}` });
    } finally {
      setBusy(false);
    }
  }

  const bannerCls = `text-sm px-4 py-2.5 rounded-xl border max-w-sm mx-auto ${tone(status.t)}`;

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 px-4 bg-surface-container-lowest">
      <div className="text-center max-w-lg">
        <div className="w-16 h-16 rounded-2xl bg-surface-container-high flex items-center justify-center mx-auto mb-4 shadow-sm border border-outline-variant/30">
          <span className="material-symbols-outlined text-primary text-3xl filled">auto_awesome</span>
        </div>
        <h1 className="font-display-lg text-display-lg text-on-surface mb-2">欢迎使用智能知识库</h1>
        <p className="text-secondary font-body-md text-body-md">AI 驱动的知识管理平台，上传文档，智能检索，流式问答。</p>
      </div>

      <div className="w-full max-w-sm bg-surface-container-lowest border border-outline-variant/40 rounded-2xl shadow-[0_8px_30px_rgba(0,0,0,0.04)] p-5">
        <form className="flex flex-col gap-4" onSubmit={submit}>
          <div className="grid grid-cols-2 gap-1.5 bg-surface-container p-1 rounded-xl">
            <button type="button" className={`py-2.5 rounded-lg font-semibold text-sm transition-all ${mode === "login" ? "bg-white text-primary shadow-sm" : "text-secondary"}`} onClick={() => setMode("login")}>登录</button>
            <button type="button" className={`py-2.5 rounded-lg font-semibold text-sm transition-all ${mode === "register" ? "bg-white text-primary shadow-sm" : "text-secondary"}`} onClick={() => setMode("register")}>注册</button>
          </div>

          {mode === "register" && (
            <label className="flex flex-col gap-1"><span className="text-xs text-secondary font-label-md">用户名</span>
              <input className="border border-outline-variant/60 rounded-xl px-4 py-2.5 text-sm bg-white focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none transition-all" minLength={3} maxLength={32} value={f.username} onChange={e => setF(c => ({ ...c, username: e.target.value }))} required />
            </label>
          )}

          <label className="flex flex-col gap-1"><span className="text-xs text-secondary font-label-md">{mode === "register" ? "邮箱" : "账号"}</span>
            <input type={mode === "register" ? "email" : "text"} className="border border-outline-variant/60 rounded-xl px-4 py-2.5 text-sm bg-white focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none transition-all" placeholder={mode === "register" ? "请输入邮箱" : "用户名或邮箱"} value={f.identity} onChange={e => setF(c => ({ ...c, identity: e.target.value }))} required />
          </label>

          <label className="flex flex-col gap-1"><span className="text-xs text-secondary font-label-md">密码</span>
            <input type="password" className="border border-outline-variant/60 rounded-xl px-4 py-2.5 text-sm bg-white focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none transition-all" minLength={8} value={f.password} onChange={e => setF(c => ({ ...c, password: e.target.value }))} required />
          </label>

          <button type="submit" disabled={busy} className="bg-primary hover:bg-primary/90 text-on-primary font-semibold rounded-xl py-3 transition-all disabled:opacity-60 flex items-center justify-center gap-2">
            {busy ? <><span className="material-symbols-outlined animate-spin text-lg">progress_activity</span> 提交中...</> : (mode === "register" ? "创建账号" : "登录")}
          </button>
        </form>
      </div>

      {status.msg && <div className={bannerCls}>{status.msg}</div>}
    </main>
  );
}

/* ── Main canvas ────────────────────────────────── */
function CanvasView({ auth, onLogout, status, setStatus }) {
  const [kbs, setKbs] = useState([]);
  const [kbId, setKbId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [docs, setDocs] = useState([]);
  const [tasks, setTasks] = useState([]);

  const [sessions, setSessions] = useState([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDocsPanel, setShowDocsPanel] = useState(false);
  const [kbForm, setKbForm] = useState({ name: "", description: "" });
  const [uploadFile, setUploadFile] = useState(null);

  const fileRef = useRef(null);
  const docFileRef = useRef(null);
  const dropFileRef = useRef(null);
  const qaRef = useRef(null);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  const activeCnt = tasks.filter(t => t.status === "PENDING" || t.status === "RUNNING").length;

  /* data loading */
  useEffect(() => {
    if (!auth?.token) return;
    let c = false;
    (async () => {
      setBusy(b => ({ ...b, list: true }));
      try {
        const r = await api("/api/v1/knowledge-bases", { token: auth.token });
        const list = r?.data ?? [];
        if (c) return;
        setKbs(list);
        setKbId(cur => cur && list.some(x => x.id === cur) ? cur : list[0]?.id ?? null);
      } catch (e) { if (!c) setStatus({ t: "danger", msg: `加载知识库失败: ${e.message}` }); }
      finally { if (!c) setBusy(b => ({ ...b, list: false })); }
    })();
    return () => { c = true; };
  }, [auth?.token]);

  useEffect(() => {
    if (!auth?.token || !kbId) { setDetail(null); setDocs([]); setTasks([]); return; }
    let c = false;
    (async () => {
      setBusy(b => ({ ...b, ws: true }));
      try {
        const [dr, docR, taskR] = await Promise.all([
          api(`/api/v1/knowledge-bases/${kbId}`, { token: auth.token }),
          api(`/api/v1/knowledge-bases/${kbId}/documents`, { token: auth.token }),
          api(`/api/v1/knowledge-bases/${kbId}/ingestion-tasks`, { token: auth.token })
        ]);
        if (c) return;
        setDetail(dr?.data ?? null);
        setDocs(docR?.data ?? []);
        setTasks(taskR?.data ?? []);
      } catch (e) { if (!c) setStatus({ t: "danger", msg: `加载失败: ${e.message}` }); }
      finally { if (!c) setBusy(b => ({ ...b, ws: false })); }
    })();
    return () => { c = true; };
  }, [auth?.token, kbId]);

  /* poll active tasks */
  useEffect(() => {
    if (!auth?.token || !kbId || activeCnt === 0) return;
    const t = setInterval(async () => {
      try {
        const [dr, docR, taskR] = await Promise.all([
          api(`/api/v1/knowledge-bases/${kbId}`, { token: auth.token }),
          api(`/api/v1/knowledge-bases/${kbId}/documents`, { token: auth.token }),
          api(`/api/v1/knowledge-bases/${kbId}/ingestion-tasks`, { token: auth.token })
        ]);
        setDetail(dr?.data ?? null);
        setDocs(docR?.data ?? []);
        setTasks(taskR?.data ?? []);
      } catch { /* silent */ }
    }, 2500);
    return () => clearInterval(t);
  }, [activeCnt, auth?.token, kbId]);

  useEffect(() => { chatEndRef.current?.scrollIntoView?.({ behavior: "smooth" }); }, [sessions]);
  useEffect(() => () => qaRef.current?.abort(), []);

  /* actions */
  async function refreshKbs(forceId) {
    if (!auth?.token) return;
    const r = await api("/api/v1/knowledge-bases", { token: auth.token });
    const list = r?.data ?? [];
    setKbs(list);
    setKbId(cur => forceId && list.some(x => x.id === forceId) ? forceId : (cur && list.some(x => x.id === cur) ? cur : list[0]?.id ?? null));
  }

  async function createKB(e) {
    e.preventDefault();
    if (!auth?.token) return;
    setBusy(b => ({ ...b, create: true }));
    try {
      const r = await api("/api/v1/knowledge-bases", { method: "POST", token: auth.token, body: JSON.stringify({ name: kbForm.name.trim(), description: kbForm.description.trim() }) });
      setKbForm({ name: "", description: "" });
      await refreshKbs(r.data.id);
      setShowCreateModal(false);
      setStatus({ t: "success", msg: `知识库“${r.data.name}”已创建` });
    } catch (e) { setStatus({ t: "danger", msg: `创建失败: ${e.message}` }); }
    finally { setBusy(b => ({ ...b, create: false })); }
  }

  async function doUpload(e, file) {
    e?.preventDefault();
    const f = file || uploadFile;
    if (!auth?.token || !kbId || !f) return;
    setBusy(b => ({ ...b, upload: true }));
    const fd = new FormData(); fd.append("file", f);
    try {
      const r = await api(`/api/v1/knowledge-bases/${kbId}/documents`, { method: "POST", token: auth.token, formData: fd });
      setUploadFile(null); if (fileRef.current) fileRef.current.value = ""; if (docFileRef.current) docFileRef.current.value = ""; if (dropFileRef.current) dropFileRef.current.value = "";
      await Promise.all([
        api(`/api/v1/knowledge-bases/${kbId}`, { token: auth.token }).then(r => setDetail(r?.data ?? null)),
        api(`/api/v1/knowledge-bases/${kbId}/documents`, { token: auth.token }).then(r => setDocs(r?.data ?? [])),
        api(`/api/v1/knowledge-bases/${kbId}/ingestion-tasks`, { token: auth.token }).then(r => setTasks(r?.data ?? []))
      ]);
      setStatus({ t: "success", msg: `已上传 ${r.data.document.originalFilename}` });
    } catch (e) { setStatus({ t: "danger", msg: `上传失败: ${e.message}` }); }
    finally { setBusy(b => ({ ...b, upload: false })); }
  }

  async function doDelete(doc) {
    if (!auth?.token || !kbId) return;
    setBusy(b => ({ ...b, delId: doc.id }));
    try {
      await api(`/api/v1/knowledge-bases/${kbId}/documents/${doc.id}`, { method: "DELETE", token: auth.token });
      const r = await api(`/api/v1/knowledge-bases/${kbId}/documents`, { token: auth.token });
      setDocs(r?.data ?? []);
      setStatus({ t: "success", msg: `已删除 ${doc.originalFilename}` });
    } catch (e) { setStatus({ t: "danger", msg: `删除失败: ${e.message}` }); }
    finally { setBusy(b => ({ ...b, delId: null })); }
  }

  async function doRetry(task) {
    if (!auth?.token || !kbId) return;
    setBusy(b => ({ ...b, retryId: task.id }));
    try {
      await api(`/api/v1/knowledge-bases/${kbId}/ingestion-tasks/${task.id}/retry`, { method: "POST", token: auth.token });
      const r = await api(`/api/v1/knowledge-bases/${kbId}/ingestion-tasks`, { token: auth.token });
      setTasks(r?.data ?? []);
      setStatus({ t: "success", msg: "已提交重试" });
    } catch (e) { setStatus({ t: "danger", msg: `重试失败: ${e.message}` }); }
    finally { setBusy(b => ({ ...b, retryId: null })); }
  }

  async function doQA(e) {
    e?.preventDefault();
    const q = question.trim();
    if (!auth?.token || !kbId || !q) return;
    qaRef.current?.abort();
    const ctrl = new AbortController(); qaRef.current = ctrl;
    const sid = crypto.randomUUID?.() ?? `id-${Date.now()}`;
    setQuestion("");
    setBusy(b => ({ ...b, qa: true }));

    setSessions(cur => [{ id: sid, question: q, answer: "", sources: [], hitCount: 0, latencyMs: 0, refused: false, status: "loading", error: null, createdAt: new Date().toISOString() }, ...cur]);

    try {
      const r = await fetch(`${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/qa`, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json", Authorization: `Bearer ${auth.token}` },
        body: JSON.stringify({ query: q }),
        signal: ctrl.signal
      });
      if (!r.ok) { const t = await r.text(); throw new Error(errMsg(t, parseJson(t))); }
      const payload = await r.json();
      const data = payload?.data ?? payload;
      setSessions(cur => cur.map(s => s.id === sid ? {
        ...s,
        answer: data.answer ?? "",
        sources: Array.isArray(data.sources) ? data.sources : [],
        hitCount: Number.isFinite(data.hitCount) ? data.hitCount : 0,
        latencyMs: Number.isFinite(data.latencyMs) ? data.latencyMs : 0,
        refused: !!data.refused,
        status: "done"
      } : s));
    } catch (err) {
      if (err.name !== "AbortError") {
        setSessions(cur => cur.map(s => s.id === sid ? { ...s, status: "error", error: err.message } : s));
      }
    } finally {
      if (qaRef.current === ctrl) qaRef.current = null;
      setBusy(b => ({ ...b, qa: false }));
    }
  }

  const owner = detail?.accessType === "OWNER";

  /* ── render ── */
  return (
    <div className="h-screen flex flex-col overflow-hidden bg-surface-container-lowest">
      {/* Header */}
      <header className="w-full h-16 flex justify-between items-center px-gutter flex-shrink-0 z-40 relative bg-surface-container-lowest border-b border-outline-variant/20">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-2xl">auto_awesome</span>
          <span className="font-headline-md text-headline-md text-on-surface font-bold tracking-tight">智能知识库</span>
        </div>
        <nav className="hidden md:flex gap-8 items-center absolute left-1/2 transform -translate-x-1/2">
          <button className={`font-label-md text-label-md relative py-1 transition-colors ${showDocsPanel ? "text-secondary hover:text-primary" : "text-primary after:content-[''] after:absolute after:-bottom-1 after:left-0 after:w-full after:h-[2px] after:bg-primary"}`} onClick={() => setShowDocsPanel(false)}>对话</button>
          <button className={`font-label-md text-label-md transition-colors ${showDocsPanel ? "text-primary after:content-[''] after:absolute after:-bottom-1 after:left-0 after:w-full after:h-[2px] after:bg-primary relative" : "text-secondary hover:text-primary"}`} onClick={() => setShowDocsPanel(true)}>文档</button>
        </nav>
        <div className="flex items-center gap-4">
          <select className="hidden md:block text-sm border border-outline-variant/40 rounded-lg pl-3 pr-8 py-1.5 bg-white text-on-surface focus:border-primary focus:ring-1 focus:ring-primary/10 outline-none max-w-[200px] truncate appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2216%22%20height%3D%2216%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23737686%22%20stroke-width%3D%222%22%3E%3Cpath%20d%3D%22m6%209%206%206%206-6%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[right_6px_center] bg-[length:16px]" value={kbId ?? ""} onChange={e => setKbId(e.target.value)}>
            {kbs.map(kb => <option key={kb.id} value={kb.id}>{kb.name}</option>)}
            {kbs.length === 0 && <option value="">无知识库</option>}
          </select>
          <button onClick={() => setShowCreateModal(true)} className="hidden md:flex items-center gap-1 text-sm font-semibold bg-primary text-on-primary px-4 py-2 rounded-xl hover:bg-primary/90 transition-colors">
            <span className="material-symbols-outlined text-lg">add</span>新建
          </button>
          <button aria-label="通知" className="text-secondary hover:text-primary transition-colors active:opacity-80 p-2 rounded-full hover:bg-surface-container-low">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <button onClick={onLogout} className="flex items-center justify-center w-8 h-8 rounded-full bg-surface-container-highest overflow-hidden active:opacity-80 transition-opacity font-bold text-sm text-secondary hover:text-primary" title="退出登录">
            {(auth?.user?.username ?? "U").slice(0, 1).toUpperCase()}
          </button>
        </div>
      </header>

      {/* Main canvas */}
      <main className="flex-1 flex flex-col relative overflow-hidden max-w-4xl mx-auto w-full pt-8 pb-4 px-4 md:px-0">

        {/* hidden file input */}
        <input type="file" ref={fileRef} className="hidden" accept=".pdf,.txt,.md,.doc,.docx,.xls,.xlsx" onChange={e => { const f = e.target.files?.[0]; if (f) doUpload(null, f); }} />

        {/* Status banner */}
        {status.msg && (
          <div className={`mb-3 px-4 py-2 rounded-xl border text-sm max-w-2xl mx-auto w-full ${tone(status.t)}`}>{status.msg}</div>
        )}

        {/* Docs panel (slide-in) */}
        {showDocsPanel && (
          <div className="mb-4 animate-fade-in">
            <div className="bg-white border border-outline-variant/30 rounded-2xl shadow-sm p-4 max-h-[60vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-headline-md text-headline-md text-on-surface">文档 <span className="text-sm font-normal text-secondary">({docs.length})</span></h3>
                {owner && docs.length > 0 && (
                  <button onClick={() => docFileRef.current?.click()} className="text-xs font-semibold text-primary hover:bg-primary/5 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1">
                    <span className="material-symbols-outlined text-sm">add</span>上传文档
                  </button>
                )}
              </div>

              {/* hidden file input — shared by compact button and dropzone */}
              <input type="file" ref={docFileRef} className="hidden" accept=".pdf,.txt,.md,.doc,.docx,.xls,.xlsx" onChange={e => {
                const f = e.target.files?.[0];
                if (f) doUpload(null, f);
              }} />

              {docs.length === 0 ? (
                /* empty state with dropzone */
                <div>
                  {owner ? (
                    <div
                      className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-all ${
                        busy.upload
                          ? "border-primary/30 bg-surface-container-low pointer-events-none"
                          : uploadFile
                          ? "border-green-400/50 bg-green-50/30"
                          : "border-outline-variant/40 hover:border-primary/50 hover:bg-surface-container-low"
                      }`}
                      onClick={() => dropFileRef.current?.click()}
                      onDragOver={e => { e.preventDefault(); }}
                      onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) doUpload(null, f); }}
                    >
                      <input type="file" ref={dropFileRef} className="hidden" accept=".pdf,.txt,.md,.doc,.docx,.xls,.xlsx" onChange={e => setUploadFile(e.target.files?.[0] ?? null)} />
                      {busy.upload ? (
                        <div className="flex items-center justify-center gap-2 text-sm text-secondary py-2">
                          <span className="material-symbols-outlined animate-spin text-lg">progress_activity</span>
                          <span>上传中…</span>
                        </div>
                      ) : uploadFile ? (
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-2 truncate">
                            <span className="material-symbols-outlined text-primary text-xl flex-shrink-0">description</span>
                            <span className="text-sm font-medium text-on-surface truncate">{uploadFile.name}</span>
                            <span className="text-xs text-secondary flex-shrink-0">{fmtBytes(uploadFile.size)}</span>
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            <button onClick={e => { e.stopPropagation(); setUploadFile(null); }} className="text-xs text-secondary hover:text-error transition-colors px-2 py-1">取消</button>
                            <button onClick={e => { e.stopPropagation(); doUpload(); }} className="text-xs font-semibold bg-primary text-on-primary px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors">上传</button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center gap-2 py-2">
                          <span className="material-symbols-outlined text-outline text-2xl">cloud_upload</span>
                          <div>
                            <span className="text-sm text-secondary">拖拽或点击上传文档</span>
                            <span className="text-xs text-outline ml-1.5">支持 PDF、DOCX、TXT、MD</span>
                          </div>
                          <span className="text-xs font-semibold text-primary bg-primary/5 px-3 py-1 rounded-lg mt-1">选择文档</span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-secondary">暂无文档，请联系拥有者上传。</p>
                  )}
                </div>
              ) : (
                /* document list */
                <div className="flex flex-col gap-2">
                  {docs.slice(0, 20).map(d => (
                    <div key={d.id} className="flex items-center justify-between text-sm py-1.5 px-2 rounded-lg hover:bg-surface-container-low transition-colors">
                      <div className="flex items-center gap-2 truncate">
                        <span className="material-symbols-outlined text-base text-secondary">description</span>
                        <span className="truncate">{d.originalFilename}</span>
                        <span className="text-xs text-secondary flex-shrink-0">{fmtBytes(d.sizeBytes)}</span>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className={`text-xs px-1.5 py-0.5 rounded-full ${d.processingStatus === "FAILED" ? "bg-error-container text-error" : d.processingStatus === "SUCCEEDED" ? "bg-green-100 text-green-700" : "bg-surface-container text-secondary"}`}>{d.processingStatus === "SUCCEEDED" ? "完成" : d.processingStatus === "FAILED" ? "失败" : d.processingStatus === "PROCESSING" ? "处理中" : "排队中"}</span>
                        {d.processingStatus === "FAILED" && <button onClick={() => doDelete(d)} disabled={busy.delId === d.id} className="text-xs text-error hover:underline">删除</button>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {/* tasks summary */}
              {tasks.filter(t => t.status === "FAILED").length > 0 && (
                <div className="mt-3 pt-3 border-t border-outline-variant/20">
                  <p className="text-xs text-secondary mb-1">失败任务</p>
                  {tasks.filter(t => t.status === "FAILED").slice(0, 5).map(t => (
                    <div key={t.id} className="flex items-center justify-between text-xs py-1">
                      <span className="text-error truncate">{t.failureMessage || t.failureCode || "未知错误"}</span>
                      <button onClick={() => doRetry(t)} disabled={busy.retryId === t.id} className="text-primary font-semibold hover:underline flex-shrink-0 ml-2">重试</button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Chat stream */}
        <div className="flex-1 overflow-y-auto px-2 md:px-8 pb-20 flex flex-col gap-8 scroll-smooth" id="chat-stream">
          {sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center mt-20 mb-10 opacity-80">
              <div className="w-16 h-16 rounded-2xl bg-surface-container-high flex items-center justify-center mb-6 shadow-sm border border-outline-variant/30">
                <span className="material-symbols-outlined text-primary text-3xl filled">auto_awesome</span>
              </div>
              <h1 className="font-display-lg text-display-lg text-on-surface text-center mb-2">今天想了解什么？</h1>
              <p className="text-secondary font-body-md text-body-md text-center max-w-md">向您的知识库提问，AI 将从已上传的文档中检索相关信息并生成答案。</p>
            </div>
          ) : null}

          {sessions.map(s => (
            <div key={s.id} className="animate-fade-in">
              {/* User message */}
              <div className="flex flex-col items-end gap-2 max-w-3xl mx-auto w-full">
                <span className="font-label-md text-label-md text-secondary">你</span>
                <div className="bg-surface-container-high text-on-surface px-5 py-3.5 rounded-2xl rounded-tr-sm max-w-[85%] shadow-sm border border-outline-variant/20">
                  <p className="font-body-md text-body-md leading-relaxed">{s.question}</p>
                </div>
              </div>

              {/* AI response */}
              <div className="flex flex-col items-start gap-2 max-w-3xl mx-auto w-full mt-6">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary text-sm filled">auto_awesome</span>
                  <span className="font-label-md text-label-md text-primary">
                    {s.status === "loading" ? "检索知识库…" : s.status === "error" ? "出错了" : "知识库助手"}
                  </span>
                  {s.status === "done" && (
                    <span className="text-[11px] text-secondary bg-surface-container px-2 py-0.5 rounded-full border border-outline-variant/30">
                      命中 {s.hitCount} · {s.latencyMs}ms
                    </span>
                  )}
                </div>

                {s.answer ? (
                  <div className={`bg-surface-container-lowest text-on-surface px-5 py-3.5 rounded-2xl rounded-tl-sm w-full border shadow-[0px_4px_12px_rgba(0,0,0,0.02)] ${s.refused ? "border-amber-200 bg-amber-50/30" : "border-outline-variant/40"}`}>
                    {s.refused && (
                      <div className="flex items-center gap-2 text-xs text-amber-700 mb-2">
                        <span className="material-symbols-outlined text-[16px]">info</span>
                        未找到足够可靠的文档证据，系统已拒绝猜测性回答。
                      </div>
                    )}
                    <p className="font-body-md text-body-md leading-relaxed whitespace-pre-wrap">{s.answer}</p>

                    {s.sources.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-outline-variant/30">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-label-md text-label-md text-secondary">引用来源</span>
                          <span className="text-[11px] text-secondary">按相似度排序</span>
                        </div>
                        <div className="grid gap-2">
                          {s.sources.map((src, i) => (
                            <details key={i} className="group rounded-xl border border-outline-variant/35 bg-surface-container-low px-3 py-2">
                              <summary className="cursor-pointer list-none flex items-center justify-between gap-3">
                                <span className="inline-flex items-center gap-2 min-w-0">
                                  <span className="material-symbols-outlined text-[16px] text-primary">description</span>
                                  <span className="text-xs font-semibold text-on-surface truncate">{src.documentName || "未命名文档"}</span>
                                  <span className="text-[11px] text-secondary flex-shrink-0">#{src.chunkIndex ?? i}</span>
                                </span>
                                <span className="text-[11px] text-primary bg-primary/5 px-2 py-0.5 rounded-full flex-shrink-0">
                                  {Number.isFinite(src.score) ? `${Math.round(src.score * 100)}%` : "source"}
                                </span>
                              </summary>
                              {src.preview && <p className="mt-2 text-xs leading-relaxed text-secondary whitespace-pre-wrap">{src.preview}</p>}
                            </details>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : s.status === "loading" ? (
                  <div className="bg-surface-container-lowest border border-outline-variant/40 rounded-2xl rounded-tl-sm w-full shadow-[0px_4px_12px_rgba(0,0,0,0.02)] px-5 py-4 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                    <span className="w-2 h-2 rounded-full bg-primary animate-pulse" style={{ animationDelay: "0.2s" }} />
                    <span className="w-2 h-2 rounded-full bg-primary animate-pulse" style={{ animationDelay: "0.4s" }} />
                  </div>
                ) : s.status === "error" ? (
                  <div className="bg-error-container/20 border border-error/20 rounded-2xl rounded-tl-sm w-full px-5 py-3.5">
                    <p className="text-sm text-error">{s.error || "发生未知错误"}</p>
                  </div>
                ) : null}

                {s.status === "done" && (
                  <div className="flex gap-2 mt-1">
                    <button onClick={() => navigator.clipboard?.writeText(s.answer)} className="text-secondary hover:text-primary transition-colors p-1" title="复制"><span className="material-symbols-outlined text-[18px]">content_copy</span></button>
                  </div>
                )}
              </div>
            </div>
          ))}

          <div ref={chatEndRef} />
        </div>

        {/* Input area */}
        <div className="absolute bottom-6 left-0 w-full px-4 md:px-8 bg-gradient-to-t from-surface-container-lowest via-surface-container-lowest to-transparent pt-10">
          <div className="max-w-3xl mx-auto w-full relative">
            <div className="bg-surface-container-lowest border border-outline-variant/50 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] focus-within:border-primary focus-within:shadow-[0_8px_30px_rgb(37,99,235,0.08)] transition-all duration-300 flex flex-col">
              <textarea
                ref={inputRef}
                className="w-full bg-transparent border-none resize-none focus:ring-0 px-5 py-4 font-body-md text-body-md text-on-surface placeholder:text-outline max-h-32 min-h-[56px]"
                placeholder="向您的文档提问…"
                rows={1}
                value={question}
                onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); doQA(); } }}
              />
              <div className="flex justify-between items-center px-3 pb-3">
                <div className="flex gap-1">
                  <button onClick={() => fileRef.current?.click()} className="p-2 text-secondary hover:text-primary hover:bg-surface-container rounded-lg transition-colors flex items-center justify-center" title="上传文档">
                    <span className="material-symbols-outlined text-[20px]">attach_file</span>
                  </button>
                </div>
                <button
                  onClick={doQA}
                  disabled={busy.qa || !question.trim()}
                  className="bg-primary hover:bg-primary/90 text-on-primary w-9 h-9 rounded-xl flex items-center justify-center transition-transform hover:scale-105 active:scale-95 shadow-sm disabled:opacity-50 disabled:hover:scale-100"
                >
                  {busy.qa ? <span className="material-symbols-outlined text-[20px] animate-spin">progress_activity</span> : <span className="material-symbols-outlined text-[20px] ml-0.5">arrow_upward</span>}
                </button>
              </div>
            </div>
            <div className="text-center mt-3">
              <span className="text-[11px] text-secondary/70 font-label-md">AI 生成内容可能不准确，请核实关键信息。</span>
            </div>
          </div>
        </div>
      </main>

      {/* Create KB modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShowCreateModal(false)}>
          <div className="bg-white border border-outline-variant/30 rounded-2xl shadow-[0_18px_38px_rgba(18,31,57,0.2)] p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-headline-md text-on-surface">创建知识库</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-secondary hover:text-primary p-1"><span className="material-symbols-outlined">close</span></button>
            </div>
            <form className="flex flex-col gap-4" onSubmit={createKB}>
              <label className="flex flex-col gap-1"><span className="text-xs text-secondary font-label-md">名称</span>
                <input className="border border-outline-variant/60 rounded-xl px-4 py-2.5 text-sm bg-white focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none" maxLength={64} value={kbForm.name} onChange={e => setKbForm(c => ({ ...c, name: e.target.value }))} required />
              </label>
              <label className="flex flex-col gap-1"><span className="text-xs text-secondary font-label-md">描述</span>
                <textarea className="border border-outline-variant/60 rounded-xl px-4 py-2.5 text-sm bg-white focus:border-primary focus:ring-2 focus:ring-primary/10 outline-none resize-none" rows={3} maxLength={240} value={kbForm.description} onChange={e => setKbForm(c => ({ ...c, description: e.target.value }))} />
              </label>
              <button type="submit" disabled={busy.create} className="bg-primary hover:bg-primary/90 text-on-primary font-semibold rounded-xl py-3 transition-all disabled:opacity-60">
                {busy.create ? "创建中…" : "创建知识库"}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Mobile bottom bar */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-outline-variant/20 px-4 py-2 flex items-center justify-around z-40">
        <button onClick={() => setShowDocsPanel(false)} className={`flex flex-col items-center gap-0.5 text-xs ${!showDocsPanel ? "text-primary" : "text-secondary"}`}>
          <span className="material-symbols-outlined text-xl">forum</span>对话
        </button>
        <button onClick={() => setShowDocsPanel(true)} className={`flex flex-col items-center gap-0.5 text-xs ${showDocsPanel ? "text-primary" : "text-secondary"}`}>
          <span className="material-symbols-outlined text-xl">description</span>文档
        </button>
        <button onClick={() => fileRef.current?.click()} className="flex flex-col items-center gap-0.5 text-xs text-secondary">
          <span className="material-symbols-outlined text-xl">upload_file</span>上传
        </button>
        <button onClick={() => setShowCreateModal(true)} className="flex flex-col items-center gap-0.5 text-xs text-secondary">
          <span className="material-symbols-outlined text-xl">add</span>新建
        </button>
      </div>
    </div>
  );
}

/* ── App shell ──────────────────────────────────── */
export default function App() {
  const [auth, setAuth] = useState(() => readAuth());
  const [status, setStatus] = useState({ t: "neutral", msg: "" });

  function logout() {
    writeAuth(null);
    setAuth(null);
    setStatus({ t: "neutral", msg: "" });
  }

  if (!auth?.token) {
    return <LoginView status={status} setStatus={setStatus} />;
  }

  return <CanvasView auth={auth} onLogout={logout} status={status} setStatus={setStatus} />;
}
