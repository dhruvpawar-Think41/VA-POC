import React, { useState, useRef, useCallback, useEffect } from "react";
import { AppBar, Toolbar, Typography, Chip, Box } from "@mui/material";
import CodeIcon from "@mui/icons-material/Code";

import Controls from "./components/Controls";
import ProblemPanel from "./components/ProblemPanel";
import Timer from "./components/Timer";
import HintsPanel from "./components/HintsPanel";
import FeedbackDialog from "./components/FeedbackDialog";
import CodeEditor from "./components/CodeEditor";
import TestResultsPanel from "./components/TestResultsPanel";

// In dev mode Vite proxies /api to the backend; in prod the same origin serves both.
const API_BASE = "";

export default function App() {
  // -- Connection state --------------------------------------------------
  const [status, setStatus] = useState("idle"); // idle | connecting | connected | error
  const pcRef = useRef(null);
  const localStreamRef = useRef(null);
  const pcIdRef = useRef(null);
  const audioRef = useRef(null);

  // -- Interview state (driven by data-channel messages) -----------------
  const [problem, setProblem] = useState(null);
  const [timerSeconds, setTimerSeconds] = useState(null);
  const [hints, setHints] = useState([]);
  const [feedback, setFeedback] = useState(null);
  const [testResults, setTestResults] = useState(null);

  // -- Code editor state -------------------------------------------------
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  const codeTimerRef = useRef(null);

  // Debounced sync: POST code to backend whenever it changes (300ms debounce)
  useEffect(() => {
    const pcId = pcIdRef.current;
    if (!pcId) return;

    if (codeTimerRef.current) clearTimeout(codeTimerRef.current);
    codeTimerRef.current = setTimeout(() => {
      fetch(`${API_BASE}/api/code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pc_id: pcId, code, language }),
      }).catch((err) => console.warn("Failed to sync code:", err));
    }, 300);

    return () => {
      if (codeTimerRef.current) clearTimeout(codeTimerRef.current);
    };
  }, [code, language]);

  // -- Data-channel message dispatcher -----------------------------------
  const handleDataChannelMessage = useCallback((event) => {
    try {
      const msg = JSON.parse(event.data);
      switch (msg.type) {
        case "problem":
          setProblem(msg);
          setHints([]);
          setFeedback(null);
          setTestResults(null);
          // Load starter code if available
          if (msg.starter_code && msg.starter_code[language]) {
            setCode(msg.starter_code[language]);
          }
          break;
        case "timer":
          setTimerSeconds(msg.minutes * 60);
          break;
        case "hint":
          setHints((prev) => [...prev, msg]);
          break;
        case "test_results":
          setTestResults(msg);
          break;
        case "end":
          setFeedback(msg);
          break;
        default:
          console.log("[data-channel] unknown message type:", msg.type);
      }
    } catch (err) {
      console.warn("[data-channel] failed to parse message:", err);
    }
  }, [language]);

  // -- Start connection --------------------------------------------------
  const handleStart = useCallback(async () => {
    setStatus("connecting");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 24000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      localStreamRef.current = stream;

      const pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      });
      pcRef.current = pc;

      stream.getTracks().forEach((track) => pc.addTrack(track, stream));

      // Remote audio track → hidden <audio> element
      pc.ontrack = (event) => {
        if (audioRef.current) {
          audioRef.current.srcObject = event.streams[0];
        }
      };

      // Create data channel so the backend can send us app messages
      // (problem, timer, hint, end). Must be created before the offer
      // so it's included in the SDP negotiation.
      const dc = pc.createDataChannel("pipecat");
      dc.onmessage = handleDataChannelMessage;

      // Trickle ICE
      pc.onicecandidate = async (event) => {
        if (event.candidate && pcIdRef.current) {
          try {
            await fetch(`${API_BASE}/api/offer`, {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                pc_id: pcIdRef.current,
                candidate: event.candidate.toJSON(),
              }),
            });
          } catch {
            // non-critical
          }
        }
      };

      pc.oniceconnectionstatechange = () => {
        const state = pc.iceConnectionState;
        if (state === "connected" || state === "completed") {
          setStatus("connected");
        } else if (state === "disconnected" || state === "failed") {
          setStatus("error");
          cleanup();
        }
      };

      // SDP exchange
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const resp = await fetch(`${API_BASE}/api/offer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sdp: offer.sdp, type: offer.type }),
      });

      if (!resp.ok) throw new Error(`Offer rejected: ${resp.status}`);

      const answer = await resp.json();
      pcIdRef.current = answer.pc_id;

      await pc.setRemoteDescription(
        new RTCSessionDescription({ sdp: answer.sdp, type: answer.type })
      );
    } catch (err) {
      console.error("Start failed:", err);
      setStatus("error");
      cleanup();
    }
  }, [handleDataChannelMessage]);

  // -- Cleanup -----------------------------------------------------------
  const cleanup = useCallback(() => {
    if (pcRef.current) {
      pcRef.current.close();
      pcRef.current = null;
    }
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((t) => t.stop());
      localStreamRef.current = null;
    }
    pcIdRef.current = null;
    if (audioRef.current) {
      audioRef.current.srcObject = null;
    }
  }, []);

  // -- Review code request -----------------------------------------------
  const handleReview = useCallback(async () => {
    const pcId = pcIdRef.current;
    if (!pcId) return;

    // Flush latest code immediately (skip debounce)
    await fetch(`${API_BASE}/api/code`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pc_id: pcId, code, language }),
    }).catch(() => {});

    // Ask the LLM to review
    await fetch(`${API_BASE}/api/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pc_id: pcId }),
    }).catch((err) => console.warn("Failed to request review:", err));
  }, [code, language]);

  const handleStop = useCallback(() => {
    cleanup();
    setStatus("idle");
    setProblem(null);
    setTimerSeconds(null);
    setHints([]);
    setFeedback(null);
    setTestResults(null);
  }, [cleanup]);

  // -- Render ------------------------------------------------------------
  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
      {/* Hidden audio element for remote (AI) audio */}
      <audio ref={audioRef} autoPlay />

      <AppBar position="static" color="transparent" elevation={0} sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Toolbar>
          <CodeIcon sx={{ mr: 1, color: "primary.main" }} />
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>
            Coding Interview
          </Typography>
          <Chip
            size="small"
            label={status === "connected" ? "Live" : status === "connecting" ? "Connecting..." : status === "error" ? "Error" : "Offline"}
            color={status === "connected" ? "success" : status === "connecting" ? "warning" : status === "error" ? "error" : "default"}
            variant={status === "connected" ? "filled" : "outlined"}
          />
        </Toolbar>
      </AppBar>

      <Box sx={{ display: "flex", gap: 3, px: 3, py: 4, height: "calc(100vh - 130px)" }}>
        {/* Left column: controls + timer */}
        <Box sx={{ width: 200, flexShrink: 0 }}>
          <Controls status={status} onStart={handleStart} onStop={handleStop} />
          {timerSeconds !== null && (
            <Box sx={{ mt: 3 }}>
              <Timer initialSeconds={timerSeconds} />
            </Box>
          )}
        </Box>

        {/* Middle column: problem + hints + test results */}
        <Box sx={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0, gap: 3 }}>
          <ProblemPanel problem={problem} />
          {hints.length > 0 && <HintsPanel hints={hints} />}
          {testResults && <TestResultsPanel testResults={testResults} />}
        </Box>

        {/* Right column: code editor */}
        <Box sx={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
          <CodeEditor
            code={code}
            onChange={setCode}
            language={language}
            onLanguageChange={setLanguage}
            onReview={handleReview}
            reviewDisabled={status !== "connected"}
          />
        </Box>
      </Box>

      {/* Feedback dialog (modal) */}
      <FeedbackDialog
        open={feedback !== null}
        feedback={feedback}
        onClose={() => setFeedback(null)}
      />
    </Box>
  );
}
