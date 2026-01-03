"""Alert management system for BAHB inspection."""

from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from loguru import logger

from bahb.core.types import Anomaly, SeverityLevel


class AlertChannel(Enum):
    """Available alert channels."""
    MQTT = "mqtt"
    WEBHOOK = "webhook"
    LOCAL = "local"
    EMAIL = "email"
    SMS = "sms"


@dataclass
class Alert:
    """Alert data structure."""
    id: str
    timestamp: datetime
    severity: SeverityLevel
    title: str
    message: str
    anomaly_id: Optional[str] = None
    location: Optional[dict] = None
    image_url: Optional[str] = None
    acknowledged: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.name,
            "title": self.title,
            "message": self.message,
            "anomaly_id": self.anomaly_id,
            "location": self.location,
            "image_url": self.image_url,
            "acknowledged": self.acknowledged,
        }


class AlertHandler(ABC):
    """Abstract base class for alert handlers."""

    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """Send alert through this channel."""
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the channel."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the channel."""
        pass


class MQTTHandler(AlertHandler):
    """MQTT alert handler."""

    def __init__(self, broker: str, port: int = 1883, topic: str = "bahb/alerts"):
        self.broker = broker
        self.port = port
        self.topic = topic
        self._client = None
        self._connected = False

    async def connect(self) -> bool:
        """Connect to MQTT broker."""
        try:
            import paho.mqtt.client as mqtt

            self._client = mqtt.Client()

            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    self._connected = True
                    logger.info(f"Connected to MQTT broker: {self.broker}")
                else:
                    logger.error(f"MQTT connection failed: {rc}")

            self._client.on_connect = on_connect
            self._client.connect_async(self.broker, self.port)
            self._client.loop_start()

            # Wait for connection
            await asyncio.sleep(1)
            return self._connected

        except ImportError:
            logger.warning("paho-mqtt not available")
            return False
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False

    async def send(self, alert: Alert) -> bool:
        """Send alert via MQTT."""
        if not self._connected or not self._client:
            return False

        try:
            payload = json.dumps(alert.to_dict())
            result = self._client.publish(self.topic, payload)
            return result.rc == 0
        except Exception as e:
            logger.error(f"MQTT publish error: {e}")
            return False


class WebhookHandler(AlertHandler):
    """Webhook alert handler."""

    def __init__(self, url: str, headers: dict = None):
        self.url = url
        self.headers = headers or {"Content-Type": "application/json"}
        self._session = None

    async def connect(self) -> bool:
        """Initialize HTTP session."""
        try:
            import aiohttp
            self._session = aiohttp.ClientSession()
            return True
        except ImportError:
            logger.warning("aiohttp not available")
            return False

    async def disconnect(self) -> None:
        """Close HTTP session."""
        if self._session:
            await self._session.close()

    async def send(self, alert: Alert) -> bool:
        """Send alert via webhook."""
        if not self._session:
            return False

        try:
            async with self._session.post(
                self.url,
                json=alert.to_dict(),
                headers=self.headers,
            ) as response:
                return response.status < 400
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False


class LocalHandler(AlertHandler):
    """Local alert handler (logging and sound)."""

    def __init__(self, sound_enabled: bool = True):
        self.sound_enabled = sound_enabled

    async def connect(self) -> bool:
        return True

    async def disconnect(self) -> None:
        pass

    async def send(self, alert: Alert) -> bool:
        """Handle alert locally."""
        # Log the alert
        log_method = {
            SeverityLevel.CRITICAL: logger.critical,
            SeverityLevel.HIGH: logger.error,
            SeverityLevel.MEDIUM: logger.warning,
            SeverityLevel.LOW: logger.info,
            SeverityLevel.INFO: logger.info,
        }.get(alert.severity, logger.info)

        log_method(f"ALERT [{alert.severity.name}]: {alert.title} - {alert.message}")

        # Play sound for critical/high alerts
        if self.sound_enabled and alert.severity.value >= SeverityLevel.HIGH.value:
            await self._play_alert_sound()

        return True

    async def _play_alert_sound(self) -> None:
        """Play alert sound (platform-dependent)."""
        try:
            import subprocess
            import sys

            if sys.platform == "linux":
                subprocess.Popen(
                    ["aplay", "-q", "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif sys.platform == "darwin":
                subprocess.Popen(
                    ["afplay", "/System/Library/Sounds/Sosumi.aiff"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass  # Ignore sound errors


class AlertManager:
    """
    Centralized alert management for BAHB system.

    Coordinates sending alerts through multiple channels based on
    severity and configuration.
    """

    def __init__(self):
        self._handlers: dict[AlertChannel, AlertHandler] = {}
        self._alert_history: list[Alert] = []
        self._max_history = 1000
        self._severity_channels: dict[SeverityLevel, list[AlertChannel]] = {
            SeverityLevel.CRITICAL: [AlertChannel.LOCAL, AlertChannel.MQTT, AlertChannel.WEBHOOK],
            SeverityLevel.HIGH: [AlertChannel.LOCAL, AlertChannel.MQTT],
            SeverityLevel.MEDIUM: [AlertChannel.LOCAL],
            SeverityLevel.LOW: [AlertChannel.LOCAL],
            SeverityLevel.INFO: [],
        }
        self._alert_count = 0

    async def initialize(
        self,
        mqtt_broker: str = None,
        webhook_url: str = None,
        local_sound: bool = True,
    ) -> None:
        """Initialize alert handlers."""
        # Always add local handler
        local = LocalHandler(sound_enabled=local_sound)
        await local.connect()
        self._handlers[AlertChannel.LOCAL] = local

        # Add MQTT if configured
        if mqtt_broker:
            mqtt = MQTTHandler(broker=mqtt_broker)
            if await mqtt.connect():
                self._handlers[AlertChannel.MQTT] = mqtt

        # Add webhook if configured
        if webhook_url:
            webhook = WebhookHandler(url=webhook_url)
            if await webhook.connect():
                self._handlers[AlertChannel.WEBHOOK] = webhook

        logger.info(f"Alert manager initialized with channels: {list(self._handlers.keys())}")

    async def shutdown(self) -> None:
        """Shutdown all handlers."""
        for handler in self._handlers.values():
            await handler.disconnect()
        self._handlers.clear()

    async def send_alert(
        self,
        severity: SeverityLevel,
        title: str,
        message: str,
        anomaly: Anomaly = None,
    ) -> str:
        """
        Send an alert through appropriate channels.

        Args:
            severity: Alert severity level
            title: Alert title
            message: Alert message
            anomaly: Optional associated anomaly

        Returns:
            Alert ID
        """
        self._alert_count += 1
        alert_id = f"BAHB-{self._alert_count:06d}"

        alert = Alert(
            id=alert_id,
            timestamp=datetime.now(),
            severity=severity,
            title=title,
            message=message,
            anomaly_id=anomaly.id if anomaly else None,
            location=anomaly.location.to_dict() if anomaly and anomaly.location else None,
        )

        # Store in history
        self._alert_history.append(alert)
        if len(self._alert_history) > self._max_history:
            self._alert_history.pop(0)

        # Send through appropriate channels
        channels = self._severity_channels.get(severity, [])
        for channel in channels:
            if channel in self._handlers:
                try:
                    await self._handlers[channel].send(alert)
                except Exception as e:
                    logger.error(f"Alert send error on {channel}: {e}")

        return alert_id

    async def alert_from_anomaly(self, anomaly: Anomaly) -> str:
        """Create and send alert from an anomaly."""
        title = f"{anomaly.severity.name} Anomaly: {anomaly.type}"
        message = anomaly.description

        return await self.send_alert(
            severity=anomaly.severity,
            title=title,
            message=message,
            anomaly=anomaly,
        )

    def get_recent_alerts(
        self,
        count: int = 10,
        min_severity: SeverityLevel = SeverityLevel.INFO,
    ) -> list[Alert]:
        """Get recent alerts filtered by severity."""
        filtered = [
            a for a in self._alert_history
            if a.severity.value >= min_severity.value
        ]
        return filtered[-count:]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self._alert_history:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def get_unacknowledged_count(self) -> dict[str, int]:
        """Get count of unacknowledged alerts by severity."""
        counts = {level.name: 0 for level in SeverityLevel}
        for alert in self._alert_history:
            if not alert.acknowledged:
                counts[alert.severity.name] += 1
        return counts
