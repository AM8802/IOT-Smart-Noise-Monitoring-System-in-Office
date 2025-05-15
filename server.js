const mqtt = require('mqtt');
const WebSocket = require('ws');
const express = require('express');

const app = express();
const port = 8884;

// MQTT Broker configuration
const mqttUrl = "https://www.mqtt-dashboard.com"; // Broker URL for TCP connection
const mqttTopic = "office_monitoring/data";
const mqttClient = mqtt.connect(mqttUrl);

// WebSocket server
const wss = new WebSocket.Server({ noServer: true });

// MQTT Client setup
mqttClient.on('connect', () => {
  console.log("Connected to HiveMQ broker.");
  mqttClient.subscribe(mqttTopic, (err) => {
    if (!err) console.log(`Subscribed to topic: ${mqttTopic}`);
  });
});

mqttClient.on('message', (topic, message) => {
  console.log(`MQTT message received: ${message.toString()}`);
  // Forward the message to all WebSocket clients
  wss.clients.forEach((ws) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(message.toString());
    }
  });
});

// HTTP server for WebSocket upgrades
const server = app.listen(port, () => {
  console.log(`Backend server running on http://localhost:${port}`);
});
server.on('upgrade', (request, socket, head) => {
  wss.handleUpgrade(request, socket, head, (ws) => {
    wss.emit('connection', ws, request);
  });
});
