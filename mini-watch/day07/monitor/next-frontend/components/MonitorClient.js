"use client";
import { useState } from "react";
import { requestJson } from "../api/client";
import NotesClient from "./NotesClient";

export default function MonitorClient() {
  const [user, setUser] = useState(null);
  const [username, setUsername] = useState("operator");
  const [password, setPassword] = useState("");
  const [events, setEvents] = useState([]);
  const [message, setMessage] = useState("");
  async function checkSession() {
    try {
      const result = await requestJson("/api/auth/me");
      setUser(result.user);
      setMessage(result.user ? "로그인 상태를 확인했습니다." : "로그인해 주세요.");
    } catch (error) { setMessage(error.message); }
  }
  async function login(event) {
    event.preventDefault();
    try {
      const result = await requestJson("/api/auth/login", "POST", { username, password });
      setUser(result.user);
      setPassword("");
      setMessage("로그인했습니다.");
    } catch (error) { setMessage(error.message); }
  }
  async function logout() {
    try {
      await requestJson("/api/auth/logout", "POST");
      setUser(null);
      setEvents([]);
      setMessage("로그아웃했습니다.");
    } catch (error) { setMessage(error.message); }
  }
  async function loadEvents() {
    try {
      const result = await requestJson("/api/events");
      setEvents(result.events);
      setMessage("요청 기록을 불러왔습니다.");
    } catch (error) { setMessage(error.message); }
  }
  return (
    <main>
      <h1>감시 서비스</h1>
      <button onClick={checkSession}>현재 로그인 확인</button>
      <p role="status">{message}</p>
      {!user ? (
        <form onSubmit={login}>
          <label>아이디<input value={username} onChange={e => setUsername(e.target.value)} /></label>
          <label>비밀번호<input type="password" value={password} onChange={e => setPassword(e.target.value)} /></label>
          <button>로그인</button>
        </form>
      ) : (
        <>
          <p>{user.username} 사용자</p>
          <button onClick={logout}>로그아웃</button>
          <h2>요청 기록</h2>
          <button onClick={loadEvents}>기록 불러오기</button>
          <div style={{overflowX:"auto"}}>
            <table><thead><tr><th>종류</th><th>방법</th><th>경로</th><th>상태</th></tr></thead>
              <tbody>{events.map(item => <tr key={item.id}><td>{item.event_type}</td><td>{item.method}</td><td>{item.path}</td><td>{item.status_code}</td></tr>)}</tbody>
            </table>
          </div>
          <h2>관찰 메모</h2>
          <NotesClient />
        </>
      )}
    </main>
  );
}
