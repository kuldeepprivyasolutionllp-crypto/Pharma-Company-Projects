import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8147";

const seededUsers = [
  { name: "Amneal Superuser", email: "superuser@amneal.com", role: "Superuser", status: "Active", lastActive: "Today, 10:12" },
  { name: "Sanjay Mehta", email: "admin@amneal.com", role: "Admin", status: "Active", lastActive: "Today, 09:42" },
  { name: "Nisha Verma", email: "manager@amneal.com", role: "Manager", status: "Active", lastActive: "Today, 08:16" },
  { name: "Amit Sharma", email: "supervisor@amneal.com", role: "Supervisor", status: "Active", lastActive: "Yesterday" },
  { name: "Riya Patel", email: "operator@amneal.com", role: "Operator", status: "Active", lastActive: "Today, 07:55" },
  { name: "Demo Amneal User", email: "demo@amneal.com", role: "Admin", status: "Active", lastActive: "Today, 10:04" },
];

const roleRows = [
  { name: "Superuser", description: "Unrestricted system access", users: 1, scope: "All facilities" },
  { name: "Admin", description: "Full system access", users: 2, scope: "All facilities" },
  { name: "Manager", description: "Operations and reporting", users: 1, scope: "Assigned facilities" },
  { name: "Supervisor", description: "Team and batch oversight", users: 1, scope: "Assigned department" },
  { name: "Operator", description: "Daily production tasks", users: 1, scope: "Assigned line" },
];

const permissionRows = [
  { name: "Dashboard overview", detail: "View operational KPIs" },
  { name: "Inventory", detail: "View and update stock" },
  { name: "Production", detail: "Manage production batches" },
  { name: "Distribution", detail: "Track shipments" },
  { name: "Reports", detail: "Create and export reports" },
  { name: "User management", detail: "Manage accounts and roles" },
];

const equipmentFallback = [
  { id: 1, asset_tag: "EQ-1001", name: "HPLC Analyzer", category: "Analytical", location: "QC Lab 1", status: "Operational", calibration_due: "2027-02-15" },
  { id: 2, asset_tag: "EQ-1002", name: "Tablet Compression Machine", category: "Production", location: "Line A", status: "Operational", calibration_due: "2026-12-08" },
  { id: 3, asset_tag: "EQ-1003", name: "Dissolution Tester", category: "Quality Control", location: "QC Lab 2", status: "Maintenance", calibration_due: "2026-11-20" },
  { id: 4, asset_tag: "EQ-1004", name: "Stability Chamber", category: "Storage", location: "Stability Room", status: "Operational", calibration_due: "2027-01-30" },
  { id: 5, asset_tag: "EQ-1005", name: "Automatic Filling Unit", category: "Packaging", location: "Line B", status: "Calibration due", calibration_due: "2026-10-12" },
];

function EquipmentPage({ token }) {
  const [equipment, setEquipment] = useState(equipmentFallback);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ asset_tag: "", name: "", category: "", location: "", status: "Operational", calibration_due: "" });
  const [message, setMessage] = useState("");
  useEffect(() => { fetch(`${API_URL}/equipment`, { headers: { Authorization: `Bearer ${token}` } }).then((response) => response.ok ? response.json() : Promise.reject()).then(setEquipment).catch(() => {}); }, [token]);
  function updateForm(event) { setForm((current) => ({ ...current, [event.target.name]: event.target.value })); }
  async function saveEquipment(event) {
    event.preventDefault(); setMessage("");
    const response = await fetch(`${API_URL}/equipment`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify(form) });
    const data = await response.json();
    if (!response.ok) { setMessage(data.detail || "Unable to add equipment"); return; }
    setEquipment((current) => [...current, data]); setForm({ asset_tag: "", name: "", category: "", location: "", status: "Operational", calibration_due: "" }); setShowForm(false);
  }
  async function removeEquipment(item) {
    if (!window.confirm(`Delete ${item.name}?`)) return;
    const response = await fetch(`${API_URL}/equipment/${item.id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
    if (response.ok) setEquipment((current) => current.filter((entry) => entry.id !== item.id)); else setMessage((await response.json()).detail || "Unable to delete equipment");
  }
  return <section className="management-page"><div className="page-heading"><div><p className="eyebrow small">ASSET REGISTER</p><h2>Pharma equipment</h2><p className="muted">Track instruments, production devices, and calibration readiness.</p></div><button className="primary-button" onClick={() => setShowForm((current) => !current)}>+ Add equipment</button></div>{showForm && <form className="inline-form equipment-form" onSubmit={saveEquipment}><input name="asset_tag" placeholder="Asset tag" value={form.asset_tag} onChange={updateForm} required /><input name="name" placeholder="Equipment name" value={form.name} onChange={updateForm} required /><input name="category" placeholder="Category" value={form.category} onChange={updateForm} required /><input name="location" placeholder="Location" value={form.location} onChange={updateForm} required /><select name="status" value={form.status} onChange={updateForm}><option>Operational</option><option>Maintenance</option><option>Calibration due</option><option>Retired</option></select><input name="calibration_due" type="date" value={form.calibration_due} onChange={updateForm} required /><button type="submit">Add device</button></form>}{message && <div className="error">{message}</div>}<div className="table-panel"><table><thead><tr><th>Asset tag</th><th>Equipment</th><th>Category</th><th>Location</th><th>Status</th><th>Calibration due</th><th>Action</th></tr></thead><tbody>{equipment.map((item) => <tr key={item.id || item.asset_tag}><td><strong>{item.asset_tag}</strong></td><td>{item.name}</td><td>{item.category}</td><td>{item.location}</td><td><span className={`equipment-status ${item.status.toLowerCase().replace(" ", "-")}`}>{item.status}</span></td><td>{item.calibration_due}</td><td><button className="table-action" onClick={() => removeEquipment(item)}>Delete</button></td></tr>)}</tbody></table></div></section>;
}

function RolePage({ token }) {
  const [roles, setRoles] = useState(roleRows.map((role, index) => ({ ...role, id: index + 1 })));
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", scope: "" });
  const [message, setMessage] = useState("");

  useEffect(() => { fetch(`${API_URL}/admin/roles`, { headers: { Authorization: `Bearer ${token}` } }).then((response) => response.ok ? response.json() : Promise.reject()).then(setRoles).catch(() => {}); }, [token]);
  function updateForm(event) { setForm((current) => ({ ...current, [event.target.name]: event.target.value })); }
  async function saveRole(event) {
    event.preventDefault(); setMessage("");
    const response = await fetch(`${API_URL}/admin/roles`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify(form) });
    const data = await response.json();
    if (!response.ok) { setMessage(data.detail || "Unable to create role"); return; }
    setRoles((current) => [...current, data]); setForm({ name: "", description: "", scope: "" }); setShowForm(false);
  }
  async function removeRole(role) {
    if (!window.confirm(`Delete ${role.name} role?`)) return;
    const response = await fetch(`${API_URL}/admin/roles/${role.id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
    if (response.ok) setRoles((current) => current.filter((item) => item.id !== role.id)); else setMessage((await response.json()).detail || "Unable to delete role");
  }
  async function editRole(role) {
    const description = window.prompt("Role description", role.description);
    const scope = description === null ? null : window.prompt("Role scope", role.scope);
    if (description === null || scope === null) return;
    const response = await fetch(`${API_URL}/admin/roles/${role.id}`, { method: "PATCH", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ description, scope }) });
    if (response.ok) { const updated = await response.json(); setRoles((current) => current.map((item) => item.id === role.id ? updated : item)); } else setMessage((await response.json()).detail || "Unable to update role");
  }
  return <section className="management-page"><div className="page-heading"><div><p className="eyebrow small">ACCESS CONTROL</p><h2>Roles</h2><p className="muted">Define access levels across the Amneal workspace.</p></div><button className="primary-button" onClick={() => setShowForm((current) => !current)}>+ Add role</button></div>{showForm && <form className="inline-form" onSubmit={saveRole}><input name="name" placeholder="Role name" value={form.name} onChange={updateForm} required /><input name="description" placeholder="Description" value={form.description} onChange={updateForm} required /><input name="scope" placeholder="Scope" value={form.scope} onChange={updateForm} required /><button type="submit">Create</button></form>}{message && <div className="error">{message}</div>}<div className="table-panel"><table><thead><tr><th>Role</th><th>Description</th><th>Users</th><th>Scope</th><th>Action</th></tr></thead><tbody>{roles.map((role) => <tr key={role.id || role.name}><td><strong>{role.name}</strong></td><td>{role.description}</td><td>{role.user_count ?? role.users}</td><td>{role.scope}</td><td><button className="table-action" onClick={() => editRole(role)}>Edit</button><button className="table-action" onClick={() => removeRole(role)}>Delete</button></td></tr>)}</tbody></table></div></section>;
}

function UsersPage({ token }) {
  const [users, setUsers] = useState(seededUsers.map((account, index) => ({ ...account, id: index + 1, full_name: account.name, is_active: true })));
  const [roles, setRoles] = useState(roleRows);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "operator" });
  const [message, setMessage] = useState("");

  useEffect(() => { const headers = { Authorization: `Bearer ${token}` }; Promise.all([fetch(`${API_URL}/admin/users`, { headers }), fetch(`${API_URL}/admin/roles`, { headers })]).then(async ([userResponse, roleResponse]) => { if (!userResponse.ok || !roleResponse.ok) throw new Error(); setUsers(await userResponse.json()); setRoles(await roleResponse.json()); }).catch(() => {}); }, [token]);
  function updateForm(event) { setForm((current) => ({ ...current, [event.target.name]: event.target.value })); }
  async function saveUser(event) {
    event.preventDefault(); setMessage("");
    const response = await fetch(`${API_URL}/admin/users`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify(form) });
    const data = await response.json();
    if (!response.ok) { setMessage(data.detail || "Unable to create user"); return; }
    setUsers((current) => [...current, data]); setForm({ full_name: "", email: "", password: "", role: "operator" }); setShowForm(false);
  }
  async function removeUser(account) {
    if (!window.confirm(`Delete ${account.full_name || account.name}?`)) return;
    const response = await fetch(`${API_URL}/admin/users/${account.id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
    if (response.ok) setUsers((current) => current.filter((item) => item.id !== account.id)); else setMessage((await response.json()).detail || "Unable to delete user");
  }
  async function editUser(account) {
    const fullName = window.prompt("Full name", account.full_name || account.name);
    if (fullName === null) return;
    const response = await fetch(`${API_URL}/admin/users/${account.id}`, { method: "PATCH", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ full_name: fullName }) });
    if (response.ok) { const updated = await response.json(); setUsers((current) => current.map((item) => item.id === account.id ? updated : item)); } else setMessage((await response.json()).detail || "Unable to update user");
  }
  return <section className="management-page"><div className="page-heading"><div><p className="eyebrow small">DIRECTORY</p><h2>Users</h2><p className="muted">Review accounts and their assigned roles.</p></div><button className="primary-button" onClick={() => setShowForm((current) => !current)}>+ Add user</button></div>{showForm && <form className="inline-form user-form" onSubmit={saveUser}><input name="full_name" placeholder="Full name" value={form.full_name} onChange={updateForm} required /><input name="email" type="email" placeholder="Email" value={form.email} onChange={updateForm} required /><input name="password" type="password" placeholder="Password" value={form.password} onChange={updateForm} minLength="8" required /><select name="role" value={form.role} onChange={updateForm}>{roles.map((role) => <option key={role.id || role.name} value={role.name.toLowerCase()}>{role.name}</option>)}</select><button type="submit">Create</button></form>}{message && <div className="error">{message}</div>}<div className="table-panel"><table><thead><tr><th>User</th><th>Email</th><th>Role</th><th>Status</th><th>Last active</th><th>Action</th></tr></thead><tbody>{users.map((account) => <tr key={account.id || account.email}><td><strong>{account.full_name || account.name}</strong></td><td>{account.email}</td><td><span className="role-pill">{account.role}</span></td><td><span className="status-dot">{account.is_active === false ? "Inactive" : "Active"}</span></td><td>{account.last_active || account.lastActive || "Never"}</td><td><button className="table-action" onClick={() => editUser(account)}>Edit</button><button className="table-action" onClick={() => removeUser(account)}>Delete</button></td></tr>)}</tbody></table></div></section>;
}

function RightsPage({ token }) {
  const [roles, setRoles] = useState(roleRows.map((role, index) => ({ ...role, id: index + 1 })));
  const [selectedRole, setSelectedRole] = useState("manager");
  const [permissions, setPermissions] = useState({ "Dashboard overview": true, Inventory: true, Production: true, Distribution: true, Reports: true, "User management": false });
  const [permissionRowsFromApi, setPermissionRowsFromApi] = useState(permissionRows.map((permission, index) => ({ ...permission, id: index + 1, allowed: permissions[permission.name] })));
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/admin/roles`, { headers: { Authorization: `Bearer ${token}` } }).then((response) => response.ok ? response.json() : Promise.reject()).then((data) => { setRoles(data); if (data.length) setSelectedRole(data.find((role) => role.name === "manager")?.id || data[0].id); }).catch(() => {});
  }, [token]);
  useEffect(() => {
    if (!selectedRole) return;
    fetch(`${API_URL}/admin/roles/${selectedRole}/rights`, { headers: { Authorization: `Bearer ${token}` } }).then((response) => response.ok ? response.json() : Promise.reject()).then((data) => { setPermissionRowsFromApi(data); setPermissions(Object.fromEntries(data.map((permission) => [permission.name, permission.allowed]))); setSaved(false); }).catch(() => {});
  }, [selectedRole, token]);
  function togglePermission(name) {
    setSaved(false);
    setPermissions((current) => ({ ...current, [name]: !current[name] }));
  }
  async function saveRights() {
    const response = await fetch(`${API_URL}/admin/roles/${selectedRole}/rights`, { method: "PUT", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ permission_ids: permissionRowsFromApi.filter((permission) => permissions[permission.name]).map((permission) => permission.id) }) });
    if (response.ok) { setPermissionRowsFromApi(await response.json()); setSaved(true); }
  }

  return <section className="management-page"><div className="page-heading"><div><p className="eyebrow small">PERMISSIONS</p><h2>Assign rights</h2><p className="muted">Choose a role and control what its members can access.</p></div><button className="primary-button" onClick={saveRights}>{saved ? "Rights saved" : "Save rights"}</button></div><div className="rights-toolbar"><label>Role<select value={selectedRole} onChange={(event) => setSelectedRole(Number(event.target.value))}>{roles.map((role) => <option key={role.id || role.name} value={role.id}>{role.name}</option>)}</select></label><span>{permissionsRowsCount(permissions)} of {permissionRowsFromApi.length} rights enabled</span></div><div className="table-panel"><table><thead><tr><th>Right</th><th>Description</th><th className="permission-column">Allow</th></tr></thead><tbody>{permissionRowsFromApi.map((permission) => <tr key={permission.id || permission.name}><td><strong>{permission.name}</strong></td><td>{permission.description || permission.detail}</td><td className="permission-column"><label className="checkbox-label"><input type="checkbox" checked={Boolean(permissions[permission.name])} onChange={() => togglePermission(permission.name)} /><span /></label></td></tr>)}</tbody></table></div></section>;
}

function permissionsRowsCount(permissions) {
  return Object.values(permissions).filter(Boolean).length;
}

function App() {
  const [user, setUser] = useState(null);
  const [mode, setMode] = useState("signin");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("demo@amneal.com");
  const [password, setPassword] = useState("Demo@123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [activePage, setActivePage] = useState("overview");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    fetch(`${API_URL}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => (response.ok ? response.json() : Promise.reject()))
      .then(setUser)
      .catch(() => localStorage.removeItem("access_token"));
  }, []);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const endpoint = mode === "signup" ? "/auth/signup" : "/auth/login";
      const payload =
        mode === "signup"
          ? { full_name: fullName, email, password }
          : { email, password };

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to authenticate");

      localStorage.setItem("access_token", data.access_token);
      setUser(data.user);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem("access_token");
    setUser(null);
  }

  if (user) {
    const statCards = [
      { label: "Active SKUs", value: "2,431", trend: "+12.4%", tone: "positive" },
      { label: "Shipment Alerts", value: "18", trend: "-4.1%", tone: "neutral" },
      { label: "Compliance Score", value: "98.6%", trend: "+1.2%", tone: "positive" },
      { label: "Open Tickets", value: "7", trend: "+2", tone: "warning" },
    ];

    return (
      <main className="dashboard-shell">
        <aside className="sidebar">
          <div className="sidebar-brand">
            <span className="logo">A</span>
            <div>
              <strong>Amneal</strong>
              <small>Operations</small>
            </div>
          </div>

          <nav className="nav">
            <button className={activePage === "overview" ? "nav-item active" : "nav-item"} onClick={() => setActivePage("overview")}>Overview</button>
            <button className="nav-item">Inventory</button>
            <button className={activePage === "equipment" ? "nav-item active" : "nav-item"} onClick={() => setActivePage("equipment")}>Equipment</button>
            <button className="nav-item">Production</button>
            <button className="nav-item">Distribution</button>
            <button className="nav-item">Reports</button>
            <span className="nav-section">Administration</span>
            <button className={activePage === "roles" ? "nav-item active" : "nav-item"} onClick={() => setActivePage("roles")}>Roles</button>
            <button className={activePage === "users" ? "nav-item active" : "nav-item"} onClick={() => setActivePage("users")}>Users</button>
            <button className={activePage === "rights" ? "nav-item active" : "nav-item"} onClick={() => setActivePage("rights")}>Assign rights</button>
          </nav>

          <div className="profile-panel">
            <span className="tag">Signed in</span>
            <strong>{user.full_name}</strong>
            <small>{user.email}</small>
            <button onClick={logout} className="secondary full-width">Sign out</button>
          </div>
        </aside>

        <section className="content">
          {activePage === "roles" && <RolePage token={localStorage.getItem("access_token")} />}
          {activePage === "users" && <UsersPage token={localStorage.getItem("access_token")} />}
          {activePage === "rights" && <RightsPage token={localStorage.getItem("access_token")} />}
          {activePage === "equipment" && <EquipmentPage token={localStorage.getItem("access_token")} />}
          {activePage === "overview" && <>
          <header className="topbar">
            <div>
              <p className="eyebrow small">Dashboard</p>
              <h2>Pharma Operations Overview</h2>
            </div>
            <button className="primary-button">+ New Report</button>
          </header>

          <div className="stats-grid">
            {statCards.map((card) => (
              <article className="stat-card" key={card.label}>
                <span>{card.label}</span>
                <strong>{card.value}</strong>
                <em className={card.tone}>{card.trend} vs last month</em>
              </article>
            ))}
          </div>

          <div className="panel-grid">
            <article className="panel large-panel">
              <div className="panel-header">
                <h3>Production Timeline</h3>
                <span>Q3</span>
              </div>
              <div className="chart-bars" aria-label="Production chart">
                <span style={{ height: "38%" }} />
                <span style={{ height: "52%" }} />
                <span style={{ height: "65%" }} />
                <span style={{ height: "60%" }} />
                <span style={{ height: "78%" }} />
                <span style={{ height: "90%" }} />
                <span style={{ height: "84%" }} />
              </div>
            </article>

            <article className="panel">
              <div className="panel-header">
                <h3>Quality Status</h3>
                <span className="badge success">Stable</span>
              </div>
              <ul className="status-list">
                <li><span>Batch QA</span><strong>93%</strong></li>
                <li><span>Cold Chain</span><strong>100%</strong></li>
                <li><span>Audit Readiness</span><strong>96%</strong></li>
              </ul>
            </article>
          </div>

          <div className="bottom-grid">
            <article className="panel">
              <div className="panel-header">
                <h3>Recent Activity</h3>
                <span>Today</span>
              </div>
              <ul className="activity-list">
                <li><strong>Batch AX-904</strong><span>Approved for release</span></li>
                <li><strong>Warehouse B</strong><span>Replenishment completed</span></li>
                <li><strong>Supplier check</strong><span>2 items flagged for review</span></li>
              </ul>
            </article>

            <article className="panel">
              <div className="panel-header">
                <h3>System Health</h3>
                <span className="badge info">Online</span>
              </div>
              <div className="health-points">
                <div><strong>42</strong><span>Systems</span></div>
                <div><strong>06</strong><span>Network checks</span></div>
                <div><strong>99.9%</strong><span>Uptime</span></div>
              </div>
            </article>
          </div>
          </>}
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <section className="card auth-card">
        <div className="brand">
          <span className="logo">A</span>
          <span>AMNEAL</span>
        </div>

        <div className="mode-toggle" role="tablist" aria-label="Authentication modes">
          <button
            type="button"
            className={mode === "signin" ? "toggle active" : "toggle"}
            onClick={() => setMode("signin")}
          >
            Sign in
          </button>
          <button
            type="button"
            className={mode === "signup" ? "toggle active" : "toggle"}
            onClick={() => setMode("signup")}
          >
            Sign up
          </button>
        </div>

        <p className="eyebrow">{mode === "signin" ? "WELCOME BACK" : "CREATE ACCOUNT"}</p>
        <h1>{mode === "signin" ? "Sign in to your account" : "Create your account"}</h1>
        <p className="muted">
          {mode === "signin"
            ? "Access your secure workspace and continue where you left off."
            : "Set up your Amneal access in a few seconds."}
        </p>

        <form onSubmit={submit}>
          {mode === "signup" && (
            <label>
              Full name
              <input
                type="text"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                required
                minLength="2"
                autoComplete="name"
              />
            </label>
          )}

          <label>
            Email address
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoComplete={mode === "signin" ? "email" : "new-email"}
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              minLength="8"
              autoComplete={mode === "signin" ? "current-password" : "new-password"}
            />
          </label>

          {error && (
            <div className="error" role="alert">
              {error}
            </div>
          )}

          <button disabled={loading} type="submit">
            {loading ? (mode === "signin" ? "Signing in..." : "Creating account...") : mode === "signin" ? "Sign in" : "Create account"}
            <span>→</span>
          </button>
        </form>

        <p className="hint">
          {mode === "signin" ? "Demo: demo@amneal.com / Demo@123" : "Use your email and a password with at least 8 characters."}
        </p>
      </section>
      <footer>© 2026 Amneal · Secure access</footer>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
