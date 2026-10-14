"use client";

import { useState } from "react";

export default function Counter() {
  const [count, setCount] = useState(0);

  function handleClick() {
    setCount(count + 1);
  }

  return (
    <div className="panel">
      <p>확인 횟수: {count}</p>
      <button onClick={handleClick}>한 번 확인</button>
    </div>
  );
}
