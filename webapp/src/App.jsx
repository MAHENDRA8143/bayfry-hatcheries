import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Chart from "chart.js/auto";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "https://bayfry-hatcheries.onrender.com").replace(/\/$/, "");

const API = {
  login: `${API_BASE}/api/auth/login`,
  current: `${API_BASE}/api/data/current?hours=96`,
  prediction: `${API_BASE}/api/predictions/next-day?history_hours=72`
};

const thresholds = {
  bod: { label: "BOD", unit: "mg/L", warning: 30, critical: 50, safe: "< 30 mg/L" },
  cod: { label: "COD", unit: "mg/L", warning: 250, critical: 400, safe: "< 250 mg/L" },
  ph: { label: "pH", unit: "", min: 7.5, max: 8.5, criticalLow: 7.0, criticalHigh: 9.0, safe: "7.5-8.5" },
  do: { label: "DO", unit: "mg/L", warning: 5, critical: 3, safe: "> 5 mg/L" },
  nh3n: { label: "NH3-N", unit: "mg/L", warning: 10, critical: 15, safe: "< 10 mg/L" },
  tp: { label: "TP", unit: "mg/L", warning: 4, critical: 6, safe: "< 4 mg/L" },
  salinity: { label: "Salinity", unit: "ppt", min: 10, max: 25, criticalLow: 8, criticalHigh: 28, safe: "10-25 ppt" },
  temperature: { label: "Temperature", unit: "deg C", min: 26, max: 32, criticalLow: 24, criticalHigh: 35, safe: "26-32 deg C" },
  alkalinity: { label: "Alkalinity", unit: "mg/L", min: 80, max: 150, criticalLow: 65, criticalHigh: 170, safe: "80-150 mg/L" },
  anomaly: { label: "Anomaly", unit: "", safe: "None" }
};

const demoUsers = {
  operator: "operator123",
  admin: "admin123"
};

const colors = {
  bod: "#39d9ff",
  cod: "#8cf77e",
  ph: "#ffd166",
  do: "#61a5ff",
  nh3n: "#ffb45c",
  tp: "#ff5c7a",
  salinity: "#27e0c0",
  temperature: "#ffb45c",
  alkalinity: "#8cf77e",
  anomaly: "#ff5c7a"
};

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("industry_token"));
  const [loginMessage, setLoginMessage] = useState("");
  const [isOpening, setIsOpening] = useState(false);
  const [activeTab, setActiveTab] = useState("home");
  const [records, setRecords] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [showForecast, setShowForecast] = useState(false);
  const [modal, setModal] = useState(null);
  const [liveModelRows, setLiveModelRows] = useState([]);

  const tableRows = useMemo(() => createRealtimeTableRows(24, records), [records]);
  const latest = records.at(-1);
  const activeAlerts = useMemo(() => records.slice(-24).flatMap(getAlertsForRecord), [records]);
  const worst = worstSeverity(activeAlerts);

  const loadDashboardData = useCallback(async () => {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    try {
      const [dataResponse, predictionResponse] = await Promise.all([
        fetch(API.current, { headers }),
        fetch(API.prediction, { headers })
      ]);
      if (!dataResponse.ok || !predictionResponse.ok) throw new Error("Backend unavailable");
      const nextRecords = normalizeApiData(await dataResponse.json());
      if (!nextRecords.length) throw new Error("Backend returned no records");
      setRecords(nextRecords);
      const nextForecast = normalizeForecast(await predictionResponse.json(), nextRecords);
      setForecast(nextForecast.length ? nextForecast : createSevenDayForecast(nextRecords));
    } catch {
      const csvRecords = await loadCsvRecords();
      const fallbackRecords = csvRecords.length ? csvRecords : createMockRecords(96);
      setRecords(fallbackRecords);
      setForecast(createSevenDayForecast(fallbackRecords));
    }
  }, [token]);

  useEffect(() => {
    if (!token) return;
    loadDashboardData();
    const timer = window.setInterval(loadDashboardData, 60 * 60 * 1000);
    return () => window.clearInterval(timer);
  }, [token, loadDashboardData]);

  useEffect(() => {
    if (!records.length) return;
    resetLiveRows(setLiveModelRows, records);
  }, [records]);

  useEffect(() => {
    if (activeTab !== "model-live") return undefined;
    const timer = window.setInterval(() => setLiveModelRows((rows) => appendLiveModelPoint(rows, records)), 2000);
    return () => window.clearInterval(timer);
  }, [activeTab, records]);

  useEffect(() => {
    const onKey = (event) => {
      if (event.key === "Escape") setModal(null);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  async function handleLogin(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const username = String(form.get("username")).trim();
    const password = String(form.get("password")).trim();
    setLoginMessage("Authenticating...");

    try {
      const response = await fetch(API.login, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      if (!response.ok) throw new Error("API login unavailable");
      const payload = await response.json();
      if (!payload.access_token) throw new Error("Missing access token");
      completeLogin(payload.access_token);
    } catch {
      if (demoUsers[username] === password) {
        completeLogin(`demo-${username}-${Date.now()}`);
      } else {
        setLoginMessage("Invalid credentials.");
      }
    }
  }

  function completeLogin(nextToken) {
    localStorage.setItem("industry_token", nextToken);
    setIsOpening(true);
    window.setTimeout(() => {
      setToken(nextToken);
      setIsOpening(false);
    }, 760);
  }

  function logout() {
    localStorage.removeItem("industry_token");
    setToken(null);
    setRecords([]);
    setForecast([]);
    setActiveTab("home");
    setShowForecast(false);
    setLoginMessage("");
  }

  return (
    <>
      <AnimatedBackground />
      {!token ? (
        <main>
          <section className="login-screen">
            <form className={`login-card glass ${isOpening ? "opening" : ""}`} aria-label="Login to BAYFRY HATCHERYS" onSubmit={handleLogin}>
              <div className="brand-mark">BH</div>
              <h1>BAYFRY HATCHERYS</h1>
              <p>Water Quality of Data</p>
              <label htmlFor="username">Username</label>
              <input id="username" name="username" type="text" autoComplete="username" defaultValue="operator" required />
              <label htmlFor="password">Password</label>
              <input id="password" name="password" type="password" autoComplete="current-password" defaultValue="operator123" required />
              <button className="primary-btn" type="submit">Login</button>
              <div className="login-message" role="status" aria-live="polite">{loginMessage}</div>
              <small>Demo credentials: operator/operator123 and admin/admin123</small>
            </form>
          </section>
        </main>
      ) : (
        <main>
          <section className="dashboard">
            <header className="topbar glass">
              <div>
                <h1>BAYFRY HATCHERYS</h1>
                <p>Smart Water Prediction Treatment</p>
              </div>
              <button className="ghost-btn" type="button" onClick={logout}>Logout</button>
            </header>

            <div className="shell">
              <nav className="tabs glass" aria-label="Dashboard sections">
                {["home", "table", "graph", "model-live", "alerts"].map((tab) => (
                  <button key={tab} className={`tab ${activeTab === tab ? "active" : ""}`} type="button" onClick={() => setActiveTab(tab)}>
                    {tabLabel(tab)}
                  </button>
                ))}
              </nav>

              {activeTab === "home" && (
                <section className="tab-panel active">
                  <div className="welcome glass">
                    <div>
                      <span className="eyebrow">Operations Console</span>
                      <h2>Wastewater prediction treatment monitor</h2>
                      <p>Live 96-hour readings with model-ready fallback data and one-hour refresh cadence.</p>
                    </div>
                    <span className={`status-pill ${worst}`}>{worst === "critical" ? "Critical Alerts" : worst === "warning" ? "Warnings Active" : "System Optimal"}</span>
                  </div>
                  <KpiGrid records={records} latest={latest} />
                  <div className="grid-two">
                    <article className="panel glass">
                      <div className="panel-head"><h3>Live Trend</h3><span>BOD and COD</span></div>
                      <ChartCanvas id="trendChart" rows={records.slice(-36)} keys={["bod", "cod"]} onAlert={(index, key) => setModal(metricModal(records, records.length - 36 + index, key))} />
                    </article>
                    <article className="panel glass operations">
                      <div className="panel-head"><h3>Plant Operations</h3><span>Unit status</span></div>
                      <ul>
                        <li><strong>Primary Clarifier</strong><span>Optimal</span></li>
                        <li><strong>Aeration Basin</strong><span>Active</span></li>
                        <li><strong>Chemical Dosing</strong><span>Auto-regulated</span></li>
                        <li><strong>Effluent Discharge</strong><span>Within Limits</span></li>
                      </ul>
                    </article>
                  </div>
                </section>
              )}

              {activeTab === "table" && (
                <section className="tab-panel active">
                  <article className="panel glass">
                    <div className="panel-head actions-head">
                      <div><h3>Water-Quality Records</h3><span>IST operational windows</span></div>
                      <button className="secondary-btn" type="button" onClick={() => setShowForecast((value) => !value)}>
                        {showForecast ? "Hide 7-Day Forecast" : "Show 7-Day Forecast"}
                      </button>
                    </div>
                    <RecordsTable rows={tableRows} onMetric={(index, key) => setModal(metricModal(tableRows, index, key))} />
                  </article>
                  {showForecast && <ForecastGrid forecast={forecast} onOpen={(day) => setModal({ type: "forecast", day })} />}
                </section>
              )}

              {activeTab === "graph" && (
                <section className="tab-panel active">
                  <div className="chart-grid">
                    <article className="panel glass">
                      <div className="panel-head"><h3>BOD & COD Levels</h3><span>Click alert points</span></div>
                      <ChartCanvas id="bodCodChart" rows={records.slice(-36)} keys={["bod", "cod"]} onAlert={(index, key) => setModal(metricModal(records, records.length - 36 + index, key))} />
                    </article>
                    <article className="panel glass">
                      <div className="panel-head"><h3>pH Levels</h3><span>Safe range 7.5-8.5</span></div>
                      <ChartCanvas id="phChart" rows={records.slice(-36)} keys={["ph"]} onAlert={(index, key) => setModal(metricModal(records, records.length - 36 + index, key))} />
                    </article>
                    <article className="panel glass wide">
                      <div className="panel-head"><h3>Nutrients & DO Levels</h3><span>NH3-N, TP, DO</span></div>
                      <ChartCanvas id="nutrientChart" rows={records.slice(-36)} keys={["nh3n", "tp", "do"]} onAlert={(index, key) => setModal(metricModal(records, records.length - 36 + index, key))} />
                    </article>
                  </div>
                </section>
              )}

              {activeTab === "model-live" && (
                <section className="tab-panel active">
                  <div className="welcome glass live-banner">
                    <div>
                      <span className="eyebrow">Prediction Stream</span>
                      <h2>Model live results</h2>
                      <p>Rolling prediction output for Salinity, Temperature, DO, pH, and Alkalinity.</p>
                    </div>
                    <span className="status-pill optimal">Running Live</span>
                  </div>
                  <ModelKpis rows={liveModelRows} />
                  <article className="panel glass">
                    <div className="panel-head">
                      <div><h3>Live Predicted Values</h3><span>Updates every 2 seconds</span></div>
                      <button className="secondary-btn" type="button" onClick={() => resetLiveRows(setLiveModelRows, records)}>Reset Stream</button>
                    </div>
                    <ChartCanvas id="modelLiveChart" rows={liveModelRows} keys={["salinity", "temperature", "do", "ph", "alkalinity"]} live />
                  </article>
                </section>
              )}

              {activeTab === "alerts" && (
                <section className="tab-panel active">
                  <AlertsList alerts={activeAlerts} />
                </section>
              )}
            </div>
          </section>
        </main>
      )}
      {modal && <Modal modal={modal} onClose={() => setModal(null)} />}
    </>
  );
}

function AnimatedBackground() {
  const bubbles = useMemo(() => Array.from({ length: 28 }, (_, i) => ({
    id: i,
    left: `${Math.random() * 100}%`,
    width: `${8 + Math.random() * 28}px`,
    height: `${8 + Math.random() * 28}px`,
    animation: `bubbles ${12 + Math.random() * 18}s linear ${-Math.random() * 20}s infinite`
  })), []);
  const particles = useMemo(() => Array.from({ length: 46 }, (_, i) => ({
    id: i,
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
    width: `${2 + Math.random() * 4}px`,
    height: `${2 + Math.random() * 4}px`,
    background: Math.random() > 0.5 ? "rgba(140,247,126,.35)" : "rgba(255,209,102,.28)",
    animation: `drift ${8 + Math.random() * 14}s ease-in-out ${-Math.random() * 12}s infinite alternate`
  })), []);

  return (
    <div className="scene" aria-hidden="true">
      <div className="water-surface" />
      <div className="caustics" />
      <div className="rays" />
      <div className="aeration aeration-one" />
      <div className="aeration aeration-two" />
      <div className="waves wave-one" />
      <div className="waves wave-two" />
      <div className="current current-one" />
      <div className="current current-two" />
      <div className="prawn prawn-one" />
      <div className="prawn prawn-two" />
      <div className="prawn prawn-three" />
      <div className="bubble-field">{bubbles.map((bubble) => <span key={bubble.id} style={{ position: "absolute", bottom: "-40px", borderRadius: "50%", border: "1px solid rgba(190,255,255,.28)", ...bubble }} />)}</div>
      <div className="particle-field">{particles.map((particle) => <span key={particle.id} style={{ position: "absolute", borderRadius: "50%", ...particle }} />)}</div>
      <div className="formula-field">
        <span style={{ "--x": "7%", "--y": "16%", "--d": "0s", "--s": 1.2 }}>O<sub>2</sub></span>
        <span style={{ "--x": "16%", "--y": "80%", "--d": "-5s", "--s": 0.92 }}>DO &gt; 5 mg/L</span>
        <span style={{ "--x": "31%", "--y": "18%", "--d": "-9s", "--s": 0.86 }}>pH 7.5-8.5</span>
        <span style={{ "--x": "70%", "--y": "13%", "--d": "-3s", "--s": 0.98 }}>NH<sub>3</sub> + H<sup>+</sup> &lt;-&gt; NH<sub>4</sub><sup>+</sup></span>
        <span style={{ "--x": "67%", "--y": "76%", "--d": "-12s", "--s": 0.96 }}>HCO<sub>3</sub><sup>-</sup></span>
        <span style={{ "--x": "91%", "--y": "39%", "--d": "-7s", "--s": 1.1 }}>CaCO<sub>3</sub></span>
        <span style={{ "--x": "39%", "--y": "90%", "--d": "-15s", "--s": 0.82 }}>Salinity 10-25 ppt</span>
        <span style={{ "--x": "88%", "--y": "86%", "--d": "-19s", "--s": 0.8 }}>CO<sub>2</sub> + H<sub>2</sub>O</span>
      </div>
    </div>
  );
}

function KpiGrid({ latest }) {
  const kpis = [["BOD Level", "bod"], ["COD Level", "cod"], ["pH Level", "ph"], ["Dissolved Oxygen", "do"]];
  if (!latest) return null;
  return (
    <div className="kpi-grid">
      {kpis.map(([title, key]) => {
        const severity = getSeverity(key, latest[key]);
        return <KpiCard key={key} title={title} metricKey={key} value={latest[key]} severity={severity} footer={`Safe ${thresholds[key].safe}`} />;
      })}
    </div>
  );
}

function ModelKpis({ rows }) {
  const latest = rows.at(-1);
  if (!latest) return null;
  return (
    <div className="kpi-grid">
      {[["Salinity", "salinity"], ["Temperature", "temperature"], ["Dissolved Oxygen", "do"], ["pH Level", "ph"], ["Alkalinity", "alkalinity"]].map(([title, key]) => {
        const severity = getSeverity(key, latest[key]);
        return <KpiCard key={key} title={title} metricKey={key} value={latest[key]} severity={severity} footer="Predicted live" />;
      })}
    </div>
  );
}

function KpiCard({ title, metricKey, value, severity, footer }) {
  return (
    <article className={`kpi-card glass ${severity}`}>
      <h3>{title}</h3>
      <div className="kpi-value">{formatMetric(metricKey, value)}</div>
      <p>{statusLabel(severity)} · {footer}</p>
    </article>
  );
}

function RecordsTable({ rows, onMetric }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Date</th><th>Time Range IST</th><th>Source</th><th>Salinity 10-25 ppt</th><th>Temperature 26-32 deg C</th><th>DO 5-15 mg/L</th><th>pH 7.5-8.5</th><th>Alkalinity 80-150 mg/L</th><th>Anomaly</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((record, rowIndex) => (
            <tr key={`${record.timestamp.toISOString()}-${rowIndex}`}>
              <td>{formatDate(record.timestamp)}</td>
              <td>{formatHourRange(record.timestamp)}</td>
              <td>{record.source}</td>
              {["salinity", "temperature", "do", "ph", "alkalinity", "anomaly"].map((key) => {
                const severity = getSeverity(key, record[key]);
                return (
                  <td key={key}>
                    <button className={`metric-cell ${severity}`} type="button" disabled={severity === "safe"} onClick={() => onMetric(rowIndex, key)}>
                      {formatMetric(key, record[key])}
                    </button>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ForecastGrid({ forecast, onOpen }) {
  return (
    <div className="forecast-grid">
      {forecast.map((day, index) => {
        const alerts = day.hours.flatMap(getAlertsForRecord);
        const severity = worstSeverity(alerts);
        return (
          <button key={day.date.toISOString()} className={`forecast-card ${severity}`} type="button" onClick={() => onOpen(day)}>
            <strong>{formatDate(day.date)}</strong>
            {statusLabel(severity)}
            <span>{alerts.length || "No"} alert triggers predicted</span>
          </button>
        );
      })}
    </div>
  );
}

function AlertsList({ alerts }) {
  if (!alerts.length) {
    return <div className="alerts-list"><article className="empty-state glass"><h3>No active warnings or critical alerts</h3><p>All wastewater treatment readings are inside operational thresholds.</p></article></div>;
  }
  return <div className="alerts-list">{alerts.map((alert, index) => <AlertCard key={`${alert.timestamp.toISOString()}-${alert.key}-${index}`} alert={alert} />)}</div>;
}

function AlertCard({ alert }) {
  return (
    <article className={`alert-card ${alert.severity}`}>
      <h3>{alert.metric} {statusLabel(alert.severity)}</h3>
      <p><strong>Value:</strong> {alert.value} · <strong>Safe range:</strong> {alert.safe}</p>
      <p><strong>Timestamp:</strong> {formatDateTime(alert.timestamp)}</p>
      <p><strong>Problem:</strong> {alert.problem}</p>
      <p><strong>Recommended actions:</strong> {alert.action}</p>
    </article>
  );
}

function ChartCanvas({ rows, keys, onAlert, live = false }) {
  const ref = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!ref.current || !rows.length) return undefined;
    chartRef.current?.destroy();
    chartRef.current = new Chart(ref.current, {
      type: "line",
      data: {
        labels: rows.map((row) => live ? formatLiveTime(row.timestamp) : formatHour(row.timestamp)),
        datasets: keys.map((key) => ({
          label: thresholds[key].label,
          data: rows.map((row) => row[key]),
          borderColor: colors[key],
          backgroundColor: `${colors[key]}33`,
          tension: 0.34,
          pointRadius: rows.map((row) => getSeverity(key, row[key]) === "safe" ? 3 : 6),
          pointBackgroundColor: rows.map((row) => {
            const severity = getSeverity(key, row[key]);
            return severity === "critical" ? "#ff5c7a" : severity === "warning" ? "#ffd166" : colors[key];
          })
        }))
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: live ? 450 : 0 },
        interaction: { mode: "nearest", intersect: true },
        plugins: { legend: { labels: { color: "#dffcff" } } },
        scales: {
          x: { ticks: { color: "#9bb6bf", maxTicksLimit: 8 }, grid: { color: "rgba(255,255,255,.06)" } },
          y: { ticks: { color: "#9bb6bf" }, grid: { color: "rgba(255,255,255,.06)" } }
        },
        onClick: (_event, elements) => {
          if (!elements.length || !onAlert) return;
          const point = elements[0];
          const key = keys[point.datasetIndex];
          const record = rows[point.index];
          if (getSeverity(key, record[key]) !== "safe") onAlert(point.index, key);
        }
      }
    });
    return () => chartRef.current?.destroy();
  }, [rows, keys, onAlert, live]);

  return <canvas ref={ref} aria-label="Water quality chart" />;
}

function Modal({ modal, onClose }) {
  const dialogRef = useRef(null);
  useEffect(() => {
    dialogRef.current?.focus();
  }, []);

  return (
    <div className="modal-root">
      <div className="modal-backdrop" onClick={onClose} />
      <section className="modal glass" role="dialog" aria-modal="true" aria-labelledby="modalTitle" tabIndex="-1" ref={dialogRef}>
        <button className="icon-btn close-btn" type="button" aria-label="Close dialog" onClick={onClose}>&times;</button>
        {modal.type === "forecast" ? <ForecastModal day={modal.day} /> : <MetricModal alert={modal.alert} />}
      </section>
    </div>
  );
}

function MetricModal({ alert }) {
  return (
    <>
      <h2 id="modalTitle">{alert.metric} {statusLabel(alert.severity)} Alert</h2>
      <AlertCard alert={alert} />
    </>
  );
}

function ForecastModal({ day }) {
  async function exportPdf() {
    const [{ jsPDF }, { default: autoTable }] = await Promise.all([
      import("jspdf"),
      import("jspdf-autotable")
    ]);
    const doc = new jsPDF();
    doc.text("BAYFRY HATCHERYS - 24 Hour Water Quality Forecast", 14, 16);
    doc.text(formatDate(day.date), 14, 24);
    autoTable(doc, {
      startY: 32,
      head: [["Time IST", "Salinity", "Temperature", "DO", "pH", "Alkalinity", "Anomaly"]],
      body: day.hours.map((hour) => [
        formatHourRange(hour.timestamp),
        formatMetric("salinity", hour.salinity),
        formatMetric("temperature", hour.temperature),
        formatMetric("do", hour.do),
        formatMetric("ph", hour.ph),
        formatMetric("alkalinity", hour.alkalinity),
        formatMetric("anomaly", hour.anomaly)
      ])
    });
    doc.save(`the-industry-forecast-${formatDate(day.date).replaceAll("/", "-")}.pdf`);
  }

  return (
    <>
      <h2 id="modalTitle">24-Hour Forecast · {formatDate(day.date)}</h2>
      <RecordsTable rows={day.hours} onMetric={() => {}} />
      <div className="modal-actions"><button className="secondary-btn" type="button" onClick={exportPdf}>Export PDF</button></div>
    </>
  );
}

function metricModal(rows, index, key) {
  const record = rows[Number(index)];
  const alert = getAlertsForRecord(record).find((item) => item.key === key);
  return alert ? { type: "metric", alert } : null;
}

async function loadCsvRecords() {
  try {
    const response = await fetch("/data/water_quality_data_20260501_190819.csv", { cache: "no-store" });
    if (!response.ok) return [];
    return parseWaterQualityCsv(await response.text()).slice(-96);
  } catch {
    return [];
  }
}

function parseWaterQualityCsv(csvText) {
  const [headerLine, ...lines] = csvText.trim().split(/\r?\n/);
  if (!headerLine || !lines.length) return [];
  const headers = headerLine.split(",").map((header) => header.trim());
  return lines.map((line, index) => {
    const values = line.split(",");
    const row = Object.fromEntries(headers.map((header, columnIndex) => [header, values[columnIndex] ?? ""]));
    const cycle = index / 5;
    const anomaly = row.Anomaly || "";
    return {
      timestamp: new Date(row.Timestamp),
      source: anomaly ? "Generated anomaly" : "Historical CSV",
      salinity: number(row.Salinity),
      temperature: number(row.Temperature),
      do: number(row.DO),
      ph: number(row.pH),
      alkalinity: number(row.Alkalinity),
      anomaly,
      bod: round(22 + Math.sin(cycle) * 4 + (anomaly ? 14 : 0)),
      cod: round(178 + Math.cos(cycle / 1.4) * 22 + (anomaly ? 92 : 0)),
      nh3n: round(6 + Math.sin(cycle / 1.6) * 1.4 + (anomaly ? 3.5 : 0), 2),
      tp: round(2.3 + Math.cos(cycle / 2.1) * 0.45 + (anomaly ? 1.1 : 0), 2)
    };
  }).filter((row) => Number.isFinite(row.timestamp.getTime()));
}

function normalizeApiData(payload) {
  const rows = Array.isArray(payload) ? payload : payload.records || payload.data || [];
  return rows.map((row, index) => ({
    timestamp: new Date(row.timestamp || row.Timestamp || Date.now() - (rows.length - index) * 3600000),
    source: row.source || row.Source || "Plant SCADA",
    bod: number(row.bod ?? row.BOD ?? row.bod_level),
    cod: number(row.cod ?? row.COD ?? row.cod_level),
    ph: number(row.ph ?? row.pH),
    do: number(row.do ?? row.DO ?? row.dissolved_oxygen),
    nh3n: number(row.nh3n ?? row["NH3-N"] ?? row.ammonia),
    tp: number(row.tp ?? row.TP ?? row.total_phosphorus),
    salinity: number(row.salinity ?? row.Salinity),
    temperature: number(row.temperature ?? row.Temperature),
    alkalinity: number(row.alkalinity ?? row.Alkalinity),
    anomaly: row.anomaly ?? row.Anomaly ?? ""
  })).filter((row) => Object.values(row).every((value) => value !== undefined));
}

function normalizeForecast(payload, records) {
  const rows = Array.isArray(payload) ? payload : payload.forecast || payload.predictions || [];
  return rows.slice(0, 7).map((row, day) => ({
    date: new Date(row.date || row.timestamp || addDays(new Date(), day + 1)),
    summary: row.summary || "Model forecast",
    hours: Array.isArray(row.hours) && row.hours.length
      ? normalizeApiData(row.hours)
      : createHourlyForecast(day + 1, records.at(-1))
  }));
}

function createMockRecords(hours) {
  const rows = [];
  const start = new Date();
  start.setMinutes(0, 0, 0);
  for (let i = hours - 1; i >= 0; i -= 1) {
    const date = new Date(start.getTime() - i * 3600000);
    const cycle = (hours - i) / 5;
    const shock = [18, 42, 71, 88].includes(hours - i);
    rows.push({
      timestamp: date,
      source: shock ? "Influent surge" : "Plant SCADA",
      bod: round(21 + Math.sin(cycle) * 5 + (shock ? 18 + Math.random() * 17 : Math.random() * 4)),
      cod: round(172 + Math.cos(cycle / 1.4) * 28 + (shock ? 108 + Math.random() * 95 : Math.random() * 18)),
      ph: round(7.35 + Math.sin(cycle / 2) * 0.45 + (shock && Math.random() > 0.5 ? 1.05 : 0), 2),
      do: round(6.9 + Math.cos(cycle / 1.8) * 0.95 - (shock ? 2.1 + Math.random() * 1.5 : Math.random() * 0.4), 2),
      nh3n: round(5.8 + Math.sin(cycle / 1.6) * 1.9 + (shock ? 5 + Math.random() * 4.5 : Math.random() * 1.1), 2),
      tp: round(2.25 + Math.cos(cycle / 2.1) * 0.7 + (shock ? 1.8 + Math.random() * 1.9 : Math.random() * 0.3), 2),
      salinity: round(18 + Math.sin(cycle / 2.2) * 0.28 + (shock && Math.random() > 0.5 ? -2.4 : Math.random() * 0.22), 2),
      temperature: round(29 + Math.cos(cycle / 2.4) * 1.7 + (shock && Math.random() > 0.45 ? 3.3 : Math.random() * 0.4), 2),
      alkalinity: round(120 + Math.sin(cycle / 2.8) * 6 + (shock && Math.random() > 0.55 ? -32 : Math.random() * 4), 2),
      anomaly: shock ? ["DO_DROP", "TEMP_SPIKE", "SALINITY_DROP", "PH_SPIKE"][Math.floor(Math.random() * 4)] : ""
    });
  }
  return rows;
}

function createRealtimeTableRows(hours, records) {
  const now = new Date();
  now.setSeconds(0, 0);
  const baseline = records.length ? records : createMockRecords(96);
  const latest = baseline.at(-1);
  return Array.from({ length: hours }, (_, hour) => {
    const source = baseline[(baseline.length - hours + hour + baseline.length) % baseline.length] || latest;
    const cycle = (now.getHours() + now.getMinutes() / 60 + hour) / 3.8;
    const predictedAnomaly = hour > 0 && Boolean(source.anomaly) && hour % 4 === 0;
    return {
      timestamp: new Date(now.getTime() + hour * 3600000),
      source: hour === 0 ? "Live current" : "Predicted",
      salinity: round((source.salinity ?? latest.salinity ?? 18) + Math.sin(cycle) * 0.18, 2),
      temperature: round((source.temperature ?? latest.temperature ?? 29) + Math.cos(cycle / 1.4) * 0.55, 2),
      do: round((source.do ?? latest.do ?? 7.5) + Math.sin(cycle / 1.2) * 0.35, 2),
      ph: round((source.ph ?? latest.ph ?? 8) + Math.cos(cycle / 1.7) * 0.05, 2),
      alkalinity: round((source.alkalinity ?? latest.alkalinity ?? 120) + Math.sin(cycle / 1.9) * 1.5, 2),
      anomaly: hour === 0 ? (latest.anomaly || "") : (predictedAnomaly ? source.anomaly : "")
    };
  });
}

function resetLiveRows(setLiveModelRows, records) {
  const now = new Date();
  now.setSeconds(0, 0);
  const seed = createRealtimeTableRows(12, records);
  setLiveModelRows(seed.map((row, index) => ({
    ...row,
    timestamp: new Date(now.getTime() - (seed.length - index - 1) * 2 * 1000),
    source: "Predicted"
  })));
}

function appendLiveModelPoint(rows, records) {
  const previous = rows.at(-1) || createRealtimeTableRows(1, records)[0];
  const t = Date.now() / 6000;
  const next = {
    timestamp: new Date(),
    source: "Predicted",
    salinity: round(previous.salinity + Math.sin(t) * 0.05 + (Math.random() - 0.5) * 0.04, 2),
    temperature: round(previous.temperature + Math.cos(t / 1.3) * 0.06 + (Math.random() - 0.5) * 0.05, 2),
    do: round(previous.do + Math.sin(t / 1.5) * 0.06 + (Math.random() - 0.5) * 0.06, 2),
    ph: round(previous.ph + Math.cos(t / 1.8) * 0.01 + (Math.random() - 0.5) * 0.01, 2),
    alkalinity: round(previous.alkalinity + Math.sin(t / 2.1) * 0.35 + (Math.random() - 0.5) * 0.18, 2),
    anomaly: ""
  };
  return [...rows, next].slice(-30);
}

function getAlertsForRecord(record) {
  if (!record) return [];
  return ["bod", "cod", "ph", "do", "nh3n", "tp", "salinity", "temperature", "alkalinity", "anomaly"].map((key) => {
    const severity = getSeverity(key, record[key]);
    if (severity === "safe") return null;
    return {
      key,
      metric: thresholds[key].label,
      value: formatMetric(key, record[key]),
      safe: thresholds[key].safe,
      severity,
      timestamp: record.timestamp,
      problem: describeProblem(key, record[key], severity),
      action: recommendedAction(key, severity)
    };
  }).filter(Boolean);
}

function getSeverity(key, value) {
  if (key === "anomaly") return value ? "warning" : "safe";
  if (value === undefined || Number.isNaN(value)) return "safe";
  if (["salinity", "temperature", "alkalinity"].includes(key)) {
    const rules = thresholds[key];
    if (value <= rules.criticalLow || value >= rules.criticalHigh) return "critical";
    if (value < rules.min || value > rules.max) return "warning";
    return "safe";
  }
  if (key === "ph") {
    if (value <= thresholds.ph.criticalLow || value >= thresholds.ph.criticalHigh) return "critical";
    if (value < thresholds.ph.min || value > thresholds.ph.max) return "warning";
    return "safe";
  }
  if (key === "do") {
    if (value <= thresholds.do.critical) return "critical";
    if (value <= thresholds.do.warning) return "warning";
    return "safe";
  }
  if (value >= thresholds[key].critical) return "critical";
  if (value >= thresholds[key].warning) return "warning";
  return "safe";
}

function worstSeverity(alerts) {
  if (alerts.some((alert) => alert.severity === "critical")) return "critical";
  if (alerts.some((alert) => alert.severity === "warning")) return "warning";
  return "optimal";
}

function statusLabel(severity) {
  return severity === "critical" ? "Critical" : severity === "warning" ? "Warning" : "Optimal";
}

function describeProblem(key, value, severity) {
  const label = thresholds[key].label;
  if (key === "anomaly") return `Detected anomaly type: ${value}.`;
  if (["salinity", "temperature", "alkalinity"].includes(key)) return `${label} is outside the hatchery safe range for stable water quality.`;
  if (key === "do") return `${label} is ${severity === "critical" ? "dangerously low" : "below target"}, reducing biological treatment efficiency.`;
  if (key === "ph") return `${label} is outside the neutral treatment band and may inhibit biomass activity.`;
  return `${label} exceeds the ${severity} threshold, indicating elevated organic or nutrient load.`;
}

function recommendedAction(key, severity) {
  const actions = {
    bod: "Increase aeration review, inspect primary clarification, and verify influent equalization.",
    cod: "Check industrial inflow, adjust chemical dosing, and confirm oxidation process performance.",
    ph: "Inspect neutralization dosing, calibrate pH probe, and isolate unusual inflow if needed.",
    do: "Raise blower output, inspect diffusers, and confirm aeration basin mixing.",
    nh3n: "Review nitrification conditions, sludge age, alkalinity, and aeration basin DO.",
    tp: "Tune phosphorus precipitation dosing and check biological phosphorus removal stability.",
    salinity: "Check dilution flow, seawater mix ratio, and incoming water salinity.",
    temperature: "Inspect heating/cooling control, shade exposure, and water exchange rate.",
    alkalinity: "Review buffer dosing and confirm alkalinity test calibration.",
    anomaly: "Review sensor traces and inspect the latest hatchery operating conditions."
  };
  return severity === "critical" ? `${actions[key]} Escalate to shift supervisor.` : actions[key];
}

function createSevenDayForecast(records) {
  return Array.from({ length: 7 }, (_, index) => ({
    date: addDays(new Date(), index + 1),
    summary: "Predicted treatment load",
    hours: createHourlyForecast(index + 1, records.at(-1))
  }));
}

function createHourlyForecast(dayOffset, base) {
  return Array.from({ length: 24 }, (_, hour) => {
    const cycle = (hour + dayOffset * 5) / 4;
    const surge = dayOffset === 3 && hour > 9 && hour < 16;
    return {
      timestamp: new Date(addDays(new Date(), dayOffset).setHours(hour, 0, 0, 0)),
      source: "Forecast model",
      bod: round((base?.bod || 24) + Math.sin(cycle) * 4 + dayOffset * 0.6 + (surge ? 14 : 0)),
      cod: round((base?.cod || 190) + Math.cos(cycle) * 24 + dayOffset * 5 + (surge ? 95 : 0)),
      ph: round(7.35 + Math.sin(cycle / 1.6) * 0.35 + (surge ? 0.6 : 0), 2),
      do: round((base?.do || 6.5) + Math.cos(cycle) * 0.55 - dayOffset * 0.08 - (surge ? 1.8 : 0), 2),
      nh3n: round((base?.nh3n || 6.2) + Math.sin(cycle / 1.2) * 1.2 + dayOffset * 0.18 + (surge ? 3.5 : 0), 2),
      tp: round((base?.tp || 2.4) + Math.cos(cycle / 1.8) * 0.45 + dayOffset * 0.08 + (surge ? 1.3 : 0), 2),
      salinity: round((base?.salinity || 18) + Math.sin(cycle / 2.2) * 0.26 + (surge ? -1.6 : 0), 2),
      temperature: round((base?.temperature || 29) + Math.cos(cycle / 2.5) * 1.2 + (surge ? 1.8 : 0), 2),
      alkalinity: round((base?.alkalinity || 120) + Math.sin(cycle / 2.7) * 5 + (surge ? -18 : 0), 2),
      anomaly: surge && hour % 3 === 0 ? "FORECAST_SURGE" : ""
    };
  });
}

function formatMetric(key, value) {
  if (key === "anomaly") return value || "None";
  const unit = thresholds[key].unit ? ` ${thresholds[key].unit}` : "";
  const digits = ["ph", "do", "nh3n", "tp", "salinity", "temperature", "alkalinity"].includes(key) ? 2 : 1;
  return `${round(value, digits)}${unit}`;
}

function formatDate(date) {
  return new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", day: "2-digit", month: "2-digit", year: "numeric" }).format(date);
}

function formatHour(date) {
  return new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", hour12: false }).format(date);
}

function formatLiveTime(date) {
  return new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(date);
}

function formatHourRange(date) {
  const end = new Date(date.getTime() + 3600000);
  return `${formatHour(date)}-${formatHour(end)}`;
}

function formatDateTime(date) {
  return `${formatDate(date)} ${formatHour(date)} IST`;
}

function tabLabel(tab) {
  return ({ home: "Home", table: "Table", graph: "Graph", "model-live": "Model Live", alerts: "Alerts" })[tab];
}

function number(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function addDays(date, days) {
  const copy = new Date(date);
  copy.setDate(copy.getDate() + days);
  return copy;
}

function round(value, digits = 1) {
  return Number(Number(value).toFixed(digits));
}
