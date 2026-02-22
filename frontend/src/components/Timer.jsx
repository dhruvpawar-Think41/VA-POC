import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent, Typography } from "@mui/material";
import TimerIcon from "@mui/icons-material/Timer";

export default function Timer({ initialSeconds }) {
  const [seconds, setSeconds] = useState(initialSeconds);
  const intervalRef = useRef(null);

  // Reset when a new timer value arrives from the backend
  useEffect(() => {
    setSeconds(initialSeconds);
  }, [initialSeconds]);

  // Countdown
  useEffect(() => {
    if (seconds <= 0) return;

    intervalRef.current = setInterval(() => {
      setSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(intervalRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(intervalRef.current);
  }, [initialSeconds]); // restart interval only when a new timer starts

  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  const display = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  const isLow = seconds > 0 && seconds < 120;

  return (
    <Card>
      <CardContent sx={{ textAlign: "center" }}>
        <TimerIcon sx={{ fontSize: 28, color: isLow ? "error.main" : "text.secondary", mb: 1 }} />
        <Typography
          variant="h3"
          fontWeight={700}
          fontFamily="monospace"
          color={isLow ? "error.main" : "text.primary"}
        >
          {display}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {seconds === 0 ? "Time's up!" : "remaining"}
        </Typography>
      </CardContent>
    </Card>
  );
}
