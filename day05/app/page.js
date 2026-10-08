import Counter from "@/components/Counter";

export default function HomePage() {
  return (
    <div>
      <h1 style={{ fontSize: "24px", fontWeight: "bold", marginBottom: "8px" }}>Next.js 홈 화면</h1>
      <p style={{ color: "#64748b", margin: 0 }}>
        App Router 기반 간단한 카운터와 메모를 관리할 수 있는 학습용 앱입니다.
      </p>

      <div className="card">
        <h2 style={{ fontSize: "18px", fontWeight: 600, marginTop: 0, marginBottom: "12px" }}>
          숫자 카운터
        </h2>
        <p style={{ color: "#64748b", fontSize: "14px", margin: "0 0 12px 0" }}>
          useState와 &quot;use client&quot;로 브라우저 상태를 관리합니다.
        </p>
        <Counter />
      </div>
    </div>
  );
}
