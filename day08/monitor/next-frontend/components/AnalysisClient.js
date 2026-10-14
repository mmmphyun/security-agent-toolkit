"use client";
import { useState } from "react";
import { requestJson } from "../api/client";

export default function AnalysisClient() {
  const [afterId, setAfterId] = useState(null);
  const [threshold, setThreshold] = useState(10);
  const [report, setReport] = useState(null);
  const [referenceTime, setReferenceTime] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function start() {
    setLoading(true);
    try {
      const state = await requestJson("/api/analysis/start");
      setAfterId(state.after_id);
      setReferenceTime(null);
      setReport(null);
      setMessage("기존 기록을 지우지 않고 새 관찰을 시작했습니다. 일반 목록을 조회한 뒤 1분 안에 분석해 주세요.");
    } catch (e) {
      setMessage(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function load() {
    setLoading(true);
    try {
      const sameWindow = referenceTime ? `&reference_time=${encodeURIComponent(referenceTime)}` : "";
      const data = await requestJson(`/api/analysis?after_id=${afterId}&threshold=${threshold}${sameWindow}`);
      setReport(data);
      if (data.reference_time && !referenceTime) {
        setReferenceTime(data.reference_time);
      }
      setMessage(data.ready ? "결과를 불러왔습니다. 같은 관찰 구간을 유지하며 기준을 비교합니다." : data.message);
    } catch (e) {
      setMessage(e.message);
    } finally {
      setLoading(false);
    }
  }

  const card = report?.card || report?.results?.[0];

  return (
    <section aria-label="분석 결과" style={{ marginTop: "2rem", borderTop: "2px solid #ccc", paddingTop: "1rem" }}>
      <h2>분석 결과</h2>
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "1rem", flexWrap: "wrap" }}>
        <button onClick={start} disabled={loading} style={{ padding: "0.4rem 0.8rem", cursor: "pointer" }}>
          새 관찰 시작
        </button>
        <label style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
          <span>HTTP 조회 기준:</span>
          <input
            aria-label="HTTP 조회 기준"
            type="number"
            min="1"
            max="100"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
            style={{ width: "60px", padding: "0.3rem" }}
          />
        </label>
        <button onClick={load} disabled={afterId === null || loading} style={{ padding: "0.4rem 0.8rem", cursor: "pointer" }}>
          분석 결과 불러오기
        </button>
      </div>

      <p role="status" style={{ color: "#0066cc", fontWeight: "bold" }}>{message}</p>
      {afterId !== null && (
        <p style={{ fontSize: "0.9rem", color: "#666" }}>
          시작 ID: <strong>{afterId}</strong> / 이후 기록·첫 결과 조회시각의 최근 60초 / 시각은 감시 DB 수신 기준
        </p>
      )}
      {referenceTime && (
        <p style={{ fontSize: "0.9rem", color: "#666" }}>
          관찰 기준시각: <strong>{referenceTime}</strong> / 새 관찰 시작 전까지 이 구간을 유지합니다.
        </p>
      )}

      {card && (
        <article
          style={{
            border: card.triggered ? "2px solid #d9534f" : "2px solid #5cb85c",
            borderRadius: "4px",
            padding: "1rem",
            margin: "1rem 0",
            backgroundColor: "#f9f9f9",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ margin: "0 0 0.5rem 0" }}>{card.rule}</h3>
            <span
              style={{
                padding: "0.2rem 0.6rem",
                borderRadius: "3px",
                fontWeight: "bold",
                backgroundColor: card.triggered ? "#d9534f" : "#5cb85c",
                color: "#fff",
              }}
            >
              {card.status}
            </span>
          </div>
          <p>출처: <strong>{card.source}</strong></p>
          <p>
            관찰값: <strong>{card.observed}</strong> / 기준: <strong>{card.threshold}회 이상</strong> ({card.triggered ? "검토 후보" : "기준 미해당"})
          </p>
          <p style={{ fontSize: "0.9rem", color: "#555" }}>기준 산출: {card.basis}</p>
          <p style={{ fontSize: "0.9rem", color: "#555" }}>{card.reason}</p>

          <details open style={{ marginTop: "1rem" }}>
            <summary style={{ cursor: "pointer", fontWeight: "bold" }}>
              근거 보기 (총 {card.records?.length || 0}행)
            </summary>
            {card.records && card.records.length > 0 ? (
              <div style={{ overflowX: "auto", marginTop: "0.5rem" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", backgroundColor: "#fff" }}>
                  <thead>
                    <tr style={{ backgroundColor: "#eee", textAlign: "left" }}>
                      <th style={{ border: "1px solid #ddd", padding: "6px" }}>ID</th>
                      <th style={{ border: "1px solid #ddd", padding: "6px" }}>수신시각</th>
                      <th style={{ border: "1px solid #ddd", padding: "6px" }}>방법</th>
                      <th style={{ border: "1px solid #ddd", padding: "6px" }}>경로</th>
                      <th style={{ border: "1px solid #ddd", padding: "6px" }}>상태</th>
                      <th style={{ border: "1px solid #ddd", padding: "6px" }}>종류</th>
                    </tr>
                  </thead>
                  <tbody>
                    {card.records.map((row) => (
                      <tr key={row.id} style={{ backgroundColor: row.status_code === 404 ? "#fff3cd" : "inherit" }}>
                        <td style={{ border: "1px solid #ddd", padding: "6px", fontFamily: "monospace" }}>{row.id}</td>
                        <td style={{ border: "1px solid #ddd", padding: "6px" }}>{row.occurred_at}</td>
                        <td style={{ border: "1px solid #ddd", padding: "6px" }}>{row.method}</td>
                        <td style={{ border: "1px solid #ddd", padding: "6px" }}>{row.path}</td>
                        <td style={{ border: "1px solid #ddd", padding: "6px", fontWeight: row.status_code === 404 ? "bold" : "normal" }}>
                          {row.status_code}
                        </td>
                        <td style={{ border: "1px solid #ddd", padding: "6px" }}>{row.kind || row.event_type}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ marginTop: "0.5rem", color: "#888" }}>해당 근거 없음</p>
            )}
          </details>
        </article>
      )}

      <p style={{ fontSize: "0.8rem", color: "#777", marginTop: "1rem" }}>
        독립된 자료의 결과를 단일 HTTP 규칙 카드로 표시합니다. 후보 표시만으로 침해를 확정하거나 자동 조치하지 않습니다.
      </p>
    </section>
  );
}
