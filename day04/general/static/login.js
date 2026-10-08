const form = document.querySelector("#login-form");
const usernameInput = document.querySelector("#username");
const passwordInput = document.querySelector("#password");
const csrfInput = document.querySelector("#csrf-token");
const result = document.querySelector("#result");
const button = form.querySelector("button");

form.addEventListener("submit", async function (event) {
    event.preventDefault();
    button.disabled = true;
    result.textContent = "로그인 확인 중입니다.";
    const data = {username: usernameInput.value, password: passwordInput.value};

    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRF-Token": csrfInput.value},
            body: JSON.stringify(data),
        });
        const answer = await response.json();
        passwordInput.value = "";
        if (response.ok) {
            window.location.href = "/";
        } else {
            result.textContent = answer.error;
        }
    } catch (error) {
        result.textContent = "서버와 통신하지 못했습니다. 서버 실행 상태를 확인해 주세요.";
    } finally {
        button.disabled = false;
    }
});
