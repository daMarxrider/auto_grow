# Feature Scope: Chili-Zelt Automatisierung

**Projekt:** Automatisierte Überwachung und Steuerung eines Chili-Anbauzelts unter Kunstlicht  
**Version:** 1.0  
**Datum:** 2026-11-06  
**Status:** Draft

---

## 1. Projektübersicht

Ziel ist die vollständige Automatisierung der Klimasteuerung und Überwachung eines Chili-Pflanzenzelts, sodass manuelle tägliche Kontrollen entfallen. Das System hält Temperatur, Luftfeuchtigkeit und VPD (Vapor Pressure Deficit) im idealen Bereich, bietet Fernüberwachung über ein Dashboard und ermöglicht später automatisches Gießen.

### Ausgangssituation
- Zelt mit Lampe, Abluft und Lüfter vorhanden
- Tägliche manuelle Kontrolle von Klima und Pflanzen nötig
- Keine Fernüberwachung möglich

### Vision
Ein selbstregulierendes System, das optimale Wachstumsbedingungen für Chili-Pflanzen hält und dem Nutzer jederzeit (auch von unterwegs) Einblick und Kontrolle gibt.

---

## 2. Ziele

### Primärziele
- Kontinuierliche Erfassung von Temperatur und Luftfeuchtigkeit im Zelt
- Automatische Berechnung und Einhaltung eines idealen VPD-Bereichs
- Automatische Regelung von Abluft und Lampenintensität
- Fernzugriff auf Live-Daten und Kamerabild über ein Dashboard (auch außerhalb des lokalen Netzwerks)

### Sekundärziele (später)
- Automatisches Gießen bei längerer Abwesenheit (> 1 Woche)
- Alarmierung bei kritischen Abweichungen

### Nicht-Ziele (Out of Scope für aktuelle Phasen)
- Vollständige Homegrow-Software mit Nährstoffmanagement
- KI-basierte Krankheitserkennung auf Kamerabildern
- Integration in bestehende Smart-Home-Systeme (Home Assistant etc.) – kann später ergänzt werden
- Steuerung mehrerer Zelte

---

## 3. Feature-Phasen

### Phase 1 – Monitoring & Sensorik (MVP)

| Feature | Beschreibung | Priorität |
|---------|--------------|-----------|
| Temperatursensor | Erfassung der Lufttemperatur im Zelt | Must |
| Luftfeuchtigkeitssensor | Erfassung der relativen Luftfeuchtigkeit | Must |
| VPD-Berechnung | Berechnung des Vapor Pressure Deficit aus Temperatur + RH | Must |
| Lokale Datenspeicherung | Speicherung der Messwerte (z. B. InfluxDB / SQLite) | Must |
| Basis-Dashboard (lokal) | Anzeige aktueller Werte und einfacher Graphen im lokalen Netzwerk | Must |

**Akzeptanzkriterien Phase 1**
- Sensoren liefern alle 30–60 Sekunden neue Werte
- VPD wird korrekt berechnet und angezeigt
- Historische Daten der letzten 7 Tage sind als Graph sichtbar

---

### Phase 2 – Automatische Regelung

| Feature | Beschreibung | Priorität |
|---------|--------------|-----------|
| Abluft-Steuerung | Automatisches Ein-/Ausschalten oder Drehzahlregelung der Abluft basierend auf Temperatur / VPD | Must |
| Lampenintensitäts-Steuerung | Dimmung der Grow-Lampe (falls dimmbar) zur Temperatur-/VPD-Regelung | Must |
| Regelalgorithmus | PID- oder schwellwertbasierte Regelung mit konfigurierbaren Idealbereichen | Must |
| Manuelle Override-Möglichkeit | Dashboard oder physischer Schalter zum manuellen Eingriff | Should |
| Sicherheitsgrenzen | Hard-Limits (z. B. max. Temperatur → Notabschaltung Lampe / max. Abluft) | Must |

**Akzeptanzkriterien Phase 2**
- System hält VPD innerhalb eines definierten Idealbereichs (z. B. 0.8–1.2 kPa, konfigurierbar)
- Regelung reagiert innerhalb weniger Minuten auf Abweichungen
- Keine kritischen Überhitzungen möglich (Sicherheitsabschaltung)

---

### Phase 3 – Fernzugriff & Kamera

| Feature | Beschreibung | Priorität |
|---------|--------------|-----------|
| Extern erreichbares Dashboard | Zugriff von außerhalb des Heimnetzwerks (VPN, Cloudflare Tunnel, Tailscale o. Ä.) | Must |
| Live-Graphen | Temperatur, Luftfeuchtigkeit, VPD über Zeit (Stunde / Tag / Woche) | Must |
| Kamera im Zelt | Regelmäßige oder On-Demand Fotos / optional Live-Stream | Must |
| Bildanzeige im Dashboard | Aktuelles Bild + optional Verlauf | Must |
| Authentifizierung | Login-Schutz für das Dashboard | Must |

**Akzeptanzkriterien Phase 3**
- Dashboard ist von unterwegs erreichbar (Handy / Laptop)
- Kamerabild aktualisiert sich mindestens alle 5–15 Minuten (oder On-Demand)
- Graphen zeigen klare Trends der letzten Tage

---

### Phase 4 – Automatisches Gießen (später)

| Feature | Beschreibung | Priorität |
|---------|--------------|-----------|
| Bodenfeuchtigkeitssensor(en) | Messung der Substratfeuchtigkeit | Should |
| Pumpe / Bewässerungssystem | Automatisches Gießen bei Unterschreitung eines Schwellwerts | Should |
| Gieß-Logik | Zeit- oder sensorbasierte Bewässerung mit Sicherheitslimits (max. Gießmenge / Tag) | Should |
| Manuelle Auslösung | Gießen per Dashboard-Button | Should |

**Akzeptanzkriterien Phase 4**
- System kann Pflanzen über 1–2 Wochen ohne manuelles Eingreifen am Leben halten
- Überwässerung wird durch Limits verhindert

---

## 4. Funktionale Anforderungen (Details)

### Sensorik
- Temperatur: Genauigkeit ±0.5 °C oder besser
- Relative Luftfeuchtigkeit: Genauigkeit ±3 % RH oder besser
- Messintervall: konfigurierbar, Standard 30–60 s
- Redundanz: optional zweiter Sensor für Ausfallsicherheit

### VPD-Steuerung
- Idealbereich konfigurierbar (z. B. vegetative Phase vs. Blüte)
- Regelung über:
  - Abluft (Hauptaktor für Feuchtigkeit & Temperatur)
  - Lampenintensität (Sekundäraktor für Temperatur)
- Soft- und Hard-Limits

### Dashboard
- Responsive (Desktop + Mobile)
- Aktuelle Werte prominent
- Historische Graphen (Temperatur, RH, VPD)
- Kamerabild
- Status der Aktoren (Abluft an/aus / %, Lampe %)
- Einstellmöglichkeiten für Idealbereiche und Regelparameter
- Optional: Push-Benachrichtigungen bei kritischen Werten

### Sicherheit & Robustheit
- Watchdog / Neustart bei Absturz des Controllers
- Notabschaltung bei Sensorausfall oder extremen Werten
- Logging aller Regelaktionen

---

## 5. Technische Überlegungen (Orientierung)

| Bereich | Mögliche Technologie |
|---------|----------------------|
| Controller | Raspberry Pi / ESP32 / Arduino + Raspberry |
| Sensoren | SHT31 / SHT40 / BME280 (Temp + RH) |
| Aktoren | Relais / PWM-Dimmer für Abluft & Lampe |
| Backend | Python (FastAPI) / Node-RED / Home Assistant |
| Datenbank | InfluxDB + Grafana oder SQLite + Custom Dashboard |
| Fernzugriff | Tailscale / Cloudflare Tunnel / WireGuard |
| Kamera | USB-Webcam oder Raspberry Pi Camera + Timelapse |

*Hinweis: Die konkrete Technologieauswahl ist nicht Teil dieses Feature Scopes und wird in der Architekturentscheidung festgehalten.*

---

## 6. Erfolgskriterien

Das Projekt gilt als erfolgreich, wenn:

1. Der Nutzer nicht mehr täglich ins Zelt schauen muss, um Klima und Pflanzenzustand zu prüfen.
2. VPD über längere Zeiträume (Tage/Wochen) stabil im Idealbereich gehalten wird.
3. Der Nutzer von unterwegs (Arbeit / Urlaub) den Zustand des Zelts (Werte + Bild) einsehen und bei Bedarf eingreifen kann.
4. Bei Abwesenheiten von > 1 Woche die Pflanzen durch automatisches Gießen versorgt werden können.

---

## 7. Offene Punkte / Entscheidungen

- [ ] Genaue Idealbereiche für VPD (vegetativ vs. blühend) definieren
- [ ] Ist die Grow-Lampe dimmbar? (PWM / 0–10 V / Triac?)
- [ ] Abluft: Ein/Aus oder stufenlos regelbar?
- [ ] Bevorzugte Lösung für externen Zugriff (einfach vs. selbst gehostet)
- [ ] Budget- und Hardware-Präferenzen
- [ ] Gewünschte Update-Frequenz des Kamerabilds

---

## 8. Nächste Schritte

1. Hardware-Auswahl (Sensoren, Controller, Kamera)
2. Aufbau der Sensorik + lokale Datenerfassung (Phase 1)
3. Implementierung der Regelungslogik (Phase 2)
4. Dashboard + Fernzugriff + Kamera (Phase 3)
5. Bewässerungsmodul (Phase 4)

---

*Dokument erstellt als Feature Scope für die iterative Umsetzung des Chili-Zelt-Automatisierungsprojekts.*
