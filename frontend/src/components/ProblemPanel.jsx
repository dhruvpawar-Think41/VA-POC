import React from "react";
import { Card, CardContent, Typography, Chip, Paper, Box } from "@mui/material";

const difficultyColor = {
  easy: "success",
  medium: "warning",
  hard: "error",
};

export default function ProblemPanel({ problem }) {
  if (!problem) {
    return (
      <Card sx={{ flex: 1, minHeight: 300, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Typography color="text.secondary" variant="body2">
          Waiting for the interviewer to select a problem...
        </Typography>
      </Card>
    );
  }

  return (
    <Card sx={{ flex: 1, overflow: "auto" }}>
      <CardContent>
        {/* Title + difficulty */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2 }}>
          <Typography variant="h6" fontWeight={700}>
            {problem.title}
          </Typography>
          <Chip
            label={problem.difficulty}
            color={difficultyColor[problem.difficulty] || "default"}
            size="small"
          />
        </Box>

        {/* Description */}
        <Typography variant="body1" sx={{ whiteSpace: "pre-line", mb: 3 }}>
          {problem.description}
        </Typography>

        {/* Examples */}
        {problem.examples?.map((example, idx) => (
          <Paper
            key={idx}
            variant="outlined"
            sx={{
              p: 2,
              mb: 1.5,
              fontFamily: "monospace",
              fontSize: "0.85rem",
              whiteSpace: "pre-wrap",
              bgcolor: "background.default",
            }}
          >
            {example}
          </Paper>
        ))}
      </CardContent>
    </Card>
  );
}
