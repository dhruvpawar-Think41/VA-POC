import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Alert,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CancelIcon from "@mui/icons-material/Cancel";
import BugReportIcon from "@mui/icons-material/BugReport";

export default function TestResultsPanel({ testResults }) {
  if (!testResults) {
    return null;
  }

  const { success, total, passed, failed, results } = testResults;
  const passRate = total > 0 ? (passed / total) * 100 : 0;

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
          <BugReportIcon color={success ? "success" : "error"} />
          <Typography variant="subtitle1" fontWeight={600}>
            Test Results
          </Typography>
          <Chip
            label={success ? "All Passed" : `${passed}/${total} Passed`}
            color={success ? "success" : "warning"}
            size="small"
          />
        </Box>

        {/* Progress bar */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              Pass Rate
            </Typography>
            <Typography variant="caption" fontWeight={600}>
              {passRate.toFixed(0)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={passRate}
            color={success ? "success" : "warning"}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        {/* Summary */}
        <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
          <Box sx={{ flex: 1, textAlign: "center", p: 1, bgcolor: "success.dark", borderRadius: 1 }}>
            <Typography variant="h6" fontWeight={700}>
              {passed}
            </Typography>
            <Typography variant="caption" color="success.light">
              Passed
            </Typography>
          </Box>
          <Box sx={{ flex: 1, textAlign: "center", p: 1, bgcolor: "error.dark", borderRadius: 1 }}>
            <Typography variant="h6" fontWeight={700}>
              {failed}
            </Typography>
            <Typography variant="caption" color="error.light">
              Failed
            </Typography>
          </Box>
        </Box>

        {/* Individual test results */}
        {results && results.length > 0 && (
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: "block" }}>
              Test Cases
            </Typography>
            {results.map((test, idx) => (
              <Accordion
                key={idx}
                defaultExpanded={!test.passed}
                sx={{
                  mb: 0.5,
                  "&:before": { display: "none" },
                  boxShadow: "none",
                  border: 1,
                  borderColor: test.passed ? "success.dark" : "error.dark",
                }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, width: "100%" }}>
                    {test.passed ? (
                      <CheckCircleIcon fontSize="small" color="success" />
                    ) : (
                      <CancelIcon fontSize="small" color="error" />
                    )}
                    <Typography variant="body2" fontWeight={500}>
                      Test Case {idx + 1}
                    </Typography>
                    {test.execution_time_ms && (
                      <Typography variant="caption" color="text.secondary" sx={{ ml: "auto" }}>
                        {test.execution_time_ms.toFixed(0)}ms
                      </Typography>
                    )}
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  {/* Input */}
                  <Box sx={{ mb: 1.5 }}>
                    <Typography variant="caption" fontWeight={600} color="text.secondary">
                      Input:
                    </Typography>
                    <Box
                      sx={{
                        mt: 0.5,
                        p: 1,
                        bgcolor: "background.default",
                        borderRadius: 1,
                        fontFamily: "monospace",
                        fontSize: "0.75rem",
                      }}
                    >
                      {JSON.stringify(test.input, null, 2)}
                    </Box>
                  </Box>

                  {/* Expected */}
                  <Box sx={{ mb: 1.5 }}>
                    <Typography variant="caption" fontWeight={600} color="success.main">
                      Expected:
                    </Typography>
                    <Box
                      sx={{
                        mt: 0.5,
                        p: 1,
                        bgcolor: "background.default",
                        borderRadius: 1,
                        fontFamily: "monospace",
                        fontSize: "0.75rem",
                      }}
                    >
                      {JSON.stringify(test.expected, null, 2)}
                    </Box>
                  </Box>

                  {/* Actual */}
                  <Box sx={{ mb: test.error ? 1.5 : 0 }}>
                    <Typography
                      variant="caption"
                      fontWeight={600}
                      color={test.passed ? "success.main" : "error.main"}
                    >
                      Actual:
                    </Typography>
                    <Box
                      sx={{
                        mt: 0.5,
                        p: 1,
                        bgcolor: "background.default",
                        borderRadius: 1,
                        fontFamily: "monospace",
                        fontSize: "0.75rem",
                        borderLeft: 3,
                        borderColor: test.passed ? "success.main" : "error.main",
                      }}
                    >
                      {test.actual !== null && test.actual !== undefined
                        ? JSON.stringify(test.actual, null, 2)
                        : "null"}
                    </Box>
                  </Box>

                  {/* Error message if present */}
                  {test.error && (
                    <Alert severity="error" sx={{ mt: 1 }}>
                      <Typography variant="caption" fontFamily="monospace">
                        {test.error}
                      </Typography>
                    </Alert>
                  )}
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
