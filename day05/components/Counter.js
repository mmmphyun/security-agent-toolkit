"use client";

import { useState } from "react";

export default function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "12px", marginTop: "12px" }}>
      <span style={{ fontSize: "20px", fontWeight: "bold", minWidth: "40px" }}>{count}</span>
      <button className="primary" onClick={() => setCount((prev) => prev + 1)}>
        증가
      </button>
      <button onClick={() => setCount(0)}>
        초기화
      </button>
    </div>
  );
}
