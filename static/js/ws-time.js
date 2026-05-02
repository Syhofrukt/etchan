(async function() {
    try {
        // Проверяем авторизацию на сервере
        const res = await fetch("/auth/session", {
            method: "GET",
            credentials: "include" // обязательно, чтобы куки отправлялись
        });

        if (!res.ok) throw new Error("Ошибка проверки сессии");

        const data = await res.json();

        if (data.authorized) {
            console.log("Пользователь авторизован, подключаем WebSocket...");
            connectWebSocket();
        } else {
            console.log("Пользователь не авторизован, WebSocket не подключается.");
        }
    } catch (error) {
        console.error("Ошибка при проверке сессии:", error);
    }

    function connectWebSocket() {
        const socket = new WebSocket("wss://" + window.location.host + "/ws/time");

        socket.onopen = () => {
            console.log("✅ WebSocket подключен");

            setInterval(() => {
                if (socket.readyState === WebSocket.OPEN) {
                    socket.send("ping");
                }
            }, 10000); // отправляем ping каждые 10 секунд
        };

        socket.onmessage = (event) => {
            console.log("Получено сообщение от сервера:", event.data);
        };

        socket.onclose = (event) => {
            console.log("❌ WebSocket отключён", event);
            // Можно добавить логику переподключения при необходимости
        };

        socket.onerror = (error) => {
            console.error("⚠️ Ошибка WebSocket:", error);
        };
    }
})();