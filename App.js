import React, { useState, useEffect } from "react";
import './App.css';

function App() {
  const [data, setData] = useState({});
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    let ws;
    let retryTimeout;

    const connectWebSocket = () => {
      ws = new WebSocket("ws://localhost:8884"); // Backend WebSocket URL

      ws.onopen = () => {
        console.log("WebSocket connection established.");
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const receivedData = JSON.parse(event.data);
          // Handle high noise alert
          if (receivedData.alert === "high_noise") {
            console.warn(`High noise level detected: ${receivedData.value} dB`);
            fetch("http://localhost:5000/noise-alert", {
              method: "POST",
            })
              .then((response) => {
                if (!response.ok) {
                  console.error("Failed to notify backend:", response.statusText);
                }
              })
              .catch((error) => console.error("Fetch error:", error));
          }
          setData(receivedData);
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };

      ws.onclose = () => {
        console.log("WebSocket connection closed. Retrying...");
        setIsConnected(false);
        retryTimeout = setTimeout(connectWebSocket, 5000); // Retry connection after 5 seconds
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        ws.close(); // Close and retry connection
      };
    };

    connectWebSocket();

    // Cleanup WebSocket on component unmount
    return () => {
      clearTimeout(retryTimeout);
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  return (
    <div className="container">
      <h1>Smart Office Monitoring System</h1>
      {isConnected ? (
        <>
          <div className="status connected">WebSocket connection established.</div>
          <h2>Real-Time Data:</h2>
          <div className="data-grid">
            <div className="data-point">
              <strong>Noise Level:</strong>
              <span>{data.noise ?? "N/A"}</span>
            </div>
            <div className="data-point">
              <strong>Temperature:</strong>
              <span>{data.temperature ?? "N/A"} °C</span>
            </div>
            <div className="data-point">
              <strong>Humidity:</strong>
              <span>{data.humidity ?? "N/A"} %</span>
            </div>
            <div className="data-point">
              <strong>Light Intensity:</strong>
              <span>{data.light ?? "N/A"}</span>
            </div>
          </div>
        </>
      ) : (
        <div className="status disconnected">WebSocket connection not established.</div>
      )}
    </div>
  );
}

export default App;
