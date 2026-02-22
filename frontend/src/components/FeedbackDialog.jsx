import React from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Button,
  Chip,
  Box,
} from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";

const scoreLabels = {
  strong_hire: { label: "Strong Hire", color: "success" },
  hire: { label: "Hire", color: "success" },
  lean_hire: { label: "Lean Hire", color: "warning" },
  lean_no_hire: { label: "Lean No Hire", color: "warning" },
  no_hire: { label: "No Hire", color: "error" },
};

export default function FeedbackDialog({ open, feedback, onClose }) {
  if (!feedback) return null;

  const scoreInfo = scoreLabels[feedback.score] || {
    label: feedback.score,
    color: "default",
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <CheckCircleIcon color="primary" />
        Interview Complete
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Assessment
          </Typography>
          <Chip label={scoreInfo.label} color={scoreInfo.color} />
        </Box>
        <Box>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Feedback
          </Typography>
          <Typography variant="body1" sx={{ whiteSpace: "pre-line" }}>
            {feedback.feedback}
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
