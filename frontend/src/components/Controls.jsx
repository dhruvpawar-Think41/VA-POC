import React from "react";
import { Card, CardContent, Typography, Button, Stack } from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import StopIcon from "@mui/icons-material/Stop";
import MicIcon from "@mui/icons-material/Mic";

export default function Controls({ status, onStart, onStop }) {
  const isIdle = status === "idle" || status === "error";
  const isConnecting = status === "connecting";
  const isConnected = status === "connected";

  return (
    <Card>
      <CardContent>
        <Stack spacing={2} alignItems="center">
          <MicIcon sx={{ fontSize: 40, color: isConnected ? "success.main" : "text.secondary" }} />
          <Typography variant="subtitle2" color="text.secondary">
            {isConnected ? "Interview in progress" : isConnecting ? "Setting up..." : "Ready to start"}
          </Typography>
          <Stack direction="row" spacing={1}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<PlayArrowIcon />}
              onClick={onStart}
              disabled={!isIdle}
            >
              Start
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<StopIcon />}
              onClick={onStop}
              disabled={!isConnected}
            >
              Stop
            </Button>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}
