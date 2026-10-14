import { useState } from "react";

export default function LoginForm(props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  function changeUsername(event) {
    setUsername(event.target.value);
  }

  function changePassword(event) {
    setPassword(event.target.value);
  }

  function handleSubmit(event) {
    event.preventDefault();
    props.onLogin(username, password);
  }

  return (
    <section className="panel">
      <h1>{props.title}</h1>
      <p className="muted">운영자 계정으로 로그인해 주세요.</p>
      <form onSubmit={handleSubmit}>
        <label>아이디<input value={username} onChange={changeUsername} autoComplete="username" /></label>
        <label>비밀번호<input type="password" value={password} onChange={changePassword} autoComplete="current-password" /></label>
        <button className="primary" type="submit" disabled={props.busy}>로그인</button>
      </form>
    </section>
  );
}
