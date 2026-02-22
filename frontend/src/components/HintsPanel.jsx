import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import LightbulbIcon from "@mui/icons-material/Lightbulb";

export default function HintsPanel({ hints }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 1.5 }}>
          Hints
        </Typography>
        {hints.map((hint, idx) => (
          <Accordion key={idx} defaultExpanded={idx === hints.length - 1}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <LightbulbIcon sx={{ mr: 1, color: "warning.main", fontSize: 20 }} />
              <Typography variant="body2" fontWeight={500}>
                Hint {hint.hint_number}
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">{hint.text}</Typography>
            </AccordionDetails>
          </Accordion>
        ))}
      </CardContent>
    </Card>
  );
}
