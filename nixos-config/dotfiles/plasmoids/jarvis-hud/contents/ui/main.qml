/*
 * JARVIS HUD — Plasma 6 applet.
 *
 * A pure view: the daemon (scripts/jarvis) pushes state over a localhost
 * WebSocket and this widget renders it. No polling, no state of its own beyond
 * the animation phase.
 *
 * Wire format, one JSON object per message:
 *   { state: "idle"|"listening"|"thinking"|"speaking"|"confirming"|"error",
 *     level: 0.0-1.0, transcript: "", reply: "", tool: "" }
 */

import QtQuick
import QtQuick.Layouts
import QtWebSockets
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.extras as PlasmaExtras
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    readonly property int hudPort: 8770

    property string assistantState: "offline"
    property real   level: 0.0
    property string transcript: ""
    property string reply: ""
    property string activeTool: ""

    // Ring colour per state. Kirigami's palette keeps this coherent with
    // whatever Plasma colour scheme is active rather than hardcoding a theme.
    readonly property color stateColor: {
        switch (assistantState) {
        case "listening":  return Kirigami.Theme.positiveTextColor
        case "thinking":   return Kirigami.Theme.highlightColor
        case "speaking":   return Kirigami.Theme.linkColor
        case "confirming": return Kirigami.Theme.neutralTextColor
        case "error":      return Kirigami.Theme.negativeTextColor
        default:           return Kirigami.Theme.disabledTextColor
        }
    }

    readonly property string stateLabel: {
        switch (assistantState) {
        case "idle":       return "Listening for the wake word"
        case "listening":  return "Listening…"
        case "thinking":   return "Thinking…"
        case "speaking":   return "Speaking"
        case "confirming": return "Waiting for confirmation"
        case "error":      return "Error"
        default:           return "Assistant not running"
        }
    }

    // ── Transport ────────────────────────────────────────────────────────────

    WebSocket {
        id: socket
        url: "ws://127.0.0.1:" + root.hudPort
        active: true

        onTextMessageReceived: (message) => {
            try {
                const data = JSON.parse(message)
                root.assistantState = data.state    !== undefined ? data.state    : root.assistantState
                root.level          = data.level    !== undefined ? data.level    : root.level
                root.transcript     = data.transcript !== undefined ? data.transcript : root.transcript
                root.reply          = data.reply    !== undefined ? data.reply    : root.reply
                root.activeTool     = data.tool     !== undefined ? data.tool     : root.activeTool
            } catch (e) {
                // A malformed frame is not worth tearing the widget down over.
            }
        }

        onStatusChanged: {
            if (status === WebSocket.Error || status === WebSocket.Closed) {
                root.assistantState = "offline"
                root.level = 0.0
                // The daemon restarts on failure; keep trying so the widget
                // recovers on its own after a rebuild or a crash.
                reconnect.start()
            }
        }
    }

    Timer {
        id: reconnect
        interval: 3000
        repeat: false
        onTriggered: {
            socket.active = false
            socket.active = true
        }
    }

    // ── Shared visual: the reactor ring ──────────────────────────────────────

    component ReactorRing: Item {
        id: ring

        property color ringColor: root.stateColor
        property real  amplitude: root.level
        property bool  busy: root.assistantState === "thinking"

        // Drives both the idle breathing and the thinking sweep.
        property real phase: 0

        NumberAnimation on phase {
            from: 0; to: 2 * Math.PI
            duration: ring.busy ? 1200 : 3600
            loops: Animation.Infinite
            running: true
        }

        onPhaseChanged: canvas.requestPaint()
        onAmplitudeChanged: canvas.requestPaint()
        onRingColorChanged: canvas.requestPaint()

        Canvas {
            id: canvas
            anchors.fill: parent
            antialiasing: true

            onPaint: {
                const ctx = getContext("2d")
                const w = width, h = height
                ctx.reset()
                ctx.clearRect(0, 0, w, h)

                const cx = w / 2, cy = h / 2
                const outer = Math.min(w, h) / 2 - 2
                if (outer <= 4) return

                // Faint track so the ring reads as a dial even when idle.
                ctx.strokeStyle = Qt.rgba(ring.ringColor.r, ring.ringColor.g,
                                          ring.ringColor.b, 0.18)
                ctx.lineWidth = Math.max(1.5, outer * 0.06)
                ctx.beginPath()
                ctx.arc(cx, cy, outer * 0.82, 0, 2 * Math.PI)
                ctx.stroke()

                // Rotating arc while thinking; a soft breathing pulse otherwise.
                ctx.strokeStyle = ring.ringColor
                ctx.lineCap = "round"
                ctx.beginPath()
                if (ring.busy) {
                    ctx.arc(cx, cy, outer * 0.82, ring.phase, ring.phase + 1.4)
                } else {
                    const breath = 0.5 + 0.5 * Math.sin(ring.phase)
                    const sweep = 2 * Math.PI * (0.15 + 0.85 * ring.amplitude)
                    ctx.globalAlpha = ring.amplitude > 0.01 ? 1.0 : 0.35 + 0.3 * breath
                    ctx.arc(cx, cy, outer * 0.82, -Math.PI / 2, -Math.PI / 2 + sweep)
                }
                ctx.stroke()
                ctx.globalAlpha = 1.0

                // Amplitude bars radiating from the centre — the "voice" of it.
                const bars = 28
                const inner = outer * 0.34
                ctx.lineWidth = Math.max(1, outer * 0.035)
                for (let i = 0; i < bars; i++) {
                    const a = (i / bars) * 2 * Math.PI
                    // Deterministic pseudo-variation so bars differ without
                    // flickering randomly frame to frame.
                    const wobble = 0.55 + 0.45 * Math.sin(a * 3 + ring.phase * 2)
                    const len = inner + outer * 0.34 * ring.amplitude * wobble
                    ctx.globalAlpha = 0.25 + 0.75 * ring.amplitude
                    ctx.beginPath()
                    ctx.moveTo(cx + Math.cos(a) * inner, cy + Math.sin(a) * inner)
                    ctx.lineTo(cx + Math.cos(a) * len,   cy + Math.sin(a) * len)
                    ctx.stroke()
                }
                ctx.globalAlpha = 1.0

                // Core.
                ctx.fillStyle = ring.ringColor
                ctx.globalAlpha = 0.55 + 0.45 * ring.amplitude
                ctx.beginPath()
                ctx.arc(cx, cy, outer * 0.16, 0, 2 * Math.PI)
                ctx.fill()
            }
        }
    }

    // ── Panel representation ─────────────────────────────────────────────────

    compactRepresentation: MouseArea {
        Layout.minimumWidth: Kirigami.Units.iconSizes.small
        Layout.minimumHeight: Kirigami.Units.iconSizes.small
        onClicked: root.expanded = !root.expanded

        ReactorRing {
            anchors.fill: parent
            anchors.margins: 1
        }
    }

    // ── Expanded representation ──────────────────────────────────────────────

    fullRepresentation: Item {
        Layout.minimumWidth:  Kirigami.Units.gridUnit * 18
        Layout.minimumHeight: Kirigami.Units.gridUnit * 20
        Layout.preferredWidth:  Kirigami.Units.gridUnit * 20
        Layout.preferredHeight: Kirigami.Units.gridUnit * 24

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.largeSpacing

            ReactorRing {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth:  Kirigami.Units.gridUnit * 9
                Layout.preferredHeight: Kirigami.Units.gridUnit * 9
            }

            PlasmaExtras.Heading {
                Layout.fillWidth: true
                level: 4
                horizontalAlignment: Text.AlignHCenter
                text: root.stateLabel
                color: root.stateColor
                elide: Text.ElideRight
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                visible: root.activeTool.length > 0
                horizontalAlignment: Text.AlignHCenter
                opacity: 0.7
                font: Kirigami.Theme.smallFont
                text: root.activeTool
                elide: Text.ElideMiddle
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Kirigami.Theme.textColor
                opacity: 0.15
            }

            // Transcript and reply. Both scroll independently so a long answer
            // never pushes the question off the widget.
            PlasmaComponents.Label {
                Layout.fillWidth: true
                visible: root.transcript.length > 0
                text: "You: " + root.transcript
                wrapMode: Text.WordWrap
                opacity: 0.75
            }

            PlasmaComponents.ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: root.reply.length > 0

                PlasmaComponents.Label {
                    width: parent.width
                    text: root.reply
                    wrapMode: Text.WordWrap
                }
            }

            Item { Layout.fillHeight: root.reply.length === 0 }
        }
    }

    toolTipMainText: "JARVIS"
    toolTipSubText: root.stateLabel
    Plasmoid.status: root.assistantState === "idle" || root.assistantState === "offline"
                     ? PlasmaCore.Types.PassiveStatus
                     : PlasmaCore.Types.ActiveStatus
}
