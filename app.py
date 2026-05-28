import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import aiohttp
import paho.mqtt.client as mqtt
from solaredge_web import SolarEdgeWeb


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(message)s",
)
_LOGGER = logging.getLogger(__name__)


def _get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _is_ev_device(device: dict[str, Any]) -> bool:
    for key in ("deviceType", "type", "name", "model", "deviceModel", "category"):
        value = device.get(key)
        if isinstance(value, str):
            lowered = value.lower()
            if "ev" in lowered or "charger" in lowered or "vehicle" in lowered:
                return True
    return False


def _extract_devices(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        for key in ("devices", "items", "data", "result"):
            nested = payload.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
            if isinstance(nested, dict):
                nested_devices = nested.get("devices")
                if isinstance(nested_devices, list):
                    return [item for item in nested_devices if isinstance(item, dict)]

    return []


def _build_payload(raw_devices: Any) -> str:
    devices = _extract_devices(raw_devices)
    ev_devices = [device for device in devices if _is_ev_device(device)]

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ev_devices": ev_devices,
    }

    return json.dumps(payload, separators=(",", ":"))


async def main() -> None:
    poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
    mqtt_host = _get_env("MQTT_HOST")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_topic = os.getenv("MQTT_TOPIC", "solaredge/ev")

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_username = os.getenv("MQTT_USERNAME")
    mqtt_password = os.getenv("MQTT_PASSWORD")
    if mqtt_username:
        mqtt_client.username_pw_set(mqtt_username, mqtt_password)

    try:
        mqtt_client.connect(mqtt_host, mqtt_port)
    except Exception as err:  # noqa: BLE001
        raise RuntimeError(f"Failed to connect to MQTT broker at {mqtt_host}:{mqtt_port}") from err
    mqtt_client.loop_start()

    try:
        async with aiohttp.ClientSession() as session:
            solaredge_client = SolarEdgeWeb(
                username=_get_env("SOLAREDGE_USERNAME"),
                password=_get_env("SOLAREDGE_PASSWORD"),
                site_id=_get_env("SOLAREDGE_SITE_ID"),
                session=session,
            )

            while True:
                try:
                    raw_devices = await solaredge_client.async_get_home_automation_devices()
                    payload = _build_payload(raw_devices)
                    mqtt_client.publish(mqtt_topic, payload=payload, qos=1, retain=False)
                    _LOGGER.info("Published EV data to topic '%s'", mqtt_topic)
                except Exception:  # noqa: BLE001
                    _LOGGER.exception("Failed to fetch/publish EV data")

                await asyncio.sleep(poll_interval)
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
