# SolarEdge_EVCharger_to_MQTT

Publishes SolarEdge EV charger data from [solaredge-web](https://github.com/Solarlibs/solaredge-web/tree/main) to an MQTT topic.

## Configuration

Set environment variables:

- `SOLAREDGE_USERNAME` (required)
- `SOLAREDGE_PASSWORD` (required)
- `SOLAREDGE_SITE_ID` (required)
- `MQTT_HOST` (required)
- `MQTT_PORT` (optional, default: `1883`)
- `MQTT_USERNAME` (optional)
- `MQTT_PASSWORD` (optional)
- `MQTT_TOPIC` (optional, default: `solaredge/ev`)
- `POLL_INTERVAL_SECONDS` (optional, default: `60`)
- `LOG_LEVEL` (optional, default: `INFO`)

## Run with Docker

```bash
docker build -t solaredge-ev-to-mqtt .
docker run --rm \
  -e SOLAREDGE_USERNAME="your-user" \
  -e SOLAREDGE_PASSWORD="your-password" \
  -e SOLAREDGE_SITE_ID="your-site-id" \
  -e MQTT_HOST="mqtt-broker" \
  -e MQTT_TOPIC="solaredge/ev" \
  solaredge-ev-to-mqtt
```

The container fetches home automation device data, filters EV-related devices, and publishes JSON payloads continuously.
