import React from "react";
import Editor from "@monaco-editor/react";
import {
  Card,
  CardContent,
  Typography,
  FormControl,
  Select,
  MenuItem,
  Box,
  Button,
} from "@mui/material";
import RateReviewIcon from "@mui/icons-material/RateReview";

const LANGUAGES = [
  { value: "python", label: "Python" },
  { value: "javascript", label: "JavaScript" },
  { value: "java", label: "Java" },
  { value: "cpp", label: "C++" },
];

export default function CodeEditor({ code, onChange, language, onLanguageChange, onReview, reviewDisabled }) {
  return (
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent sx={{ display: "flex", flexDirection: "column", height: "100%", p: 2, "&:last-child": { pb: 2 } }}>
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1 }}>
          <Typography variant="subtitle2" color="text.secondary">
            Code Editor
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Button
              size="small"
              variant="contained"
              startIcon={<RateReviewIcon />}
              onClick={onReview}
              disabled={reviewDisabled}
            >
              Review My Code
            </Button>
            <FormControl size="small">
              <Select
                value={language}
                onChange={(e) => onLanguageChange(e.target.value)}
                sx={{ minWidth: 130, fontSize: "0.85rem" }}
              >
                {LANGUAGES.map((lang) => (
                  <MenuItem key={lang.value} value={lang.value}>
                    {lang.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>
        <Box sx={{ flexGrow: 1, minHeight: 400, border: 1, borderColor: "divider", borderRadius: 1, overflow: "hidden" }}>
          <Editor
            height="100%"
            language={language}
            theme="vs-dark"
            value={code}
            onChange={(value) => onChange(value || "")}
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              scrollBeyondLastLine: false,
              automaticLayout: true,
              tabSize: 4,
            }}
          />
        </Box>
      </CardContent>
    </Card>
  );
}
