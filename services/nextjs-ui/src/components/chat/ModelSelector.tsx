/**
 * Model Selector Component
 * Dropdown to select AI model with clear chat button
 */

'use client';

import * as React from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  SelectChangeEvent,
} from '@mui/material';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';

interface ModelSelectorProps {
  selectedModel: string;
  onModelChange: (model: string) => void;
  onClearChat: () => void;
}

const AVAILABLE_MODELS = [
  { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku' },
  { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet' },
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'gemini/gemini-1.5-pro-latest', label: 'Gemini 1.5 Pro' },
  { value: 'gemini/gemini-1.5-flash-latest', label: 'Gemini 1.5 Flash' },
];

export function ModelSelector({ selectedModel, onModelChange, onClearChat }: ModelSelectorProps) {
  const handleChange = (event: SelectChangeEvent) => {
    onModelChange(event.target.value);
  };

  return (
    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
      <FormControl sx={{ minWidth: 250 }}>
        <InputLabel id="model-select-label">AI 模型</InputLabel>
        <Select
          labelId="model-select-label"
          id="model-select"
          value={selectedModel}
          label="AI 模型"
          onChange={handleChange}
        >
          {AVAILABLE_MODELS.map((model) => (
            <MenuItem key={model.value} value={model.value}>
              {model.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <Button
        variant="outlined"
        color="error"
        startIcon={<DeleteOutlineIcon />}
        onClick={onClearChat}
      >
        清除對話
      </Button>
    </Box>
  );
}
