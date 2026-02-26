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
  CircularProgress,
} from '@mui/material';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import axios from 'axios';
import { useI18n } from '@/lib/i18n';

interface ModelSelectorProps {
  selectedModel: string;
  onModelChange: (model: string) => void;
  onClearChat: () => void;
}

interface ModelOption {
  model_name: string;
  display_name?: string;
  visible?: boolean;
}

export function ModelSelector({ selectedModel, onModelChange, onClearChat }: ModelSelectorProps) {
  const { t } = useI18n();
  const [models, setModels] = React.useState<ModelOption[]>([]);
  const [loading, setLoading] = React.useState(true);

  // Load models from config
  React.useEffect(() => {
    async function loadModels() {
      try {
        // Try to load from litellm config file
        const response = await axios.get('/config/litellm-config.yaml', {
          transformResponse: [(data) => data], // Get raw text
        });

        // Parse YAML manually (simple parsing for model_list)
        const lines = response.data.split('\n');
        const modelList: ModelOption[] = [];
        let currentModel: Partial<ModelOption> = {};

        for (const line of lines) {
          if (line.trim().startsWith('- model_name:')) {
            if (currentModel.model_name) {
              modelList.push(currentModel as ModelOption);
            }
            currentModel = { model_name: line.split(':').slice(1).join(':').trim() };
          } else if (line.trim().startsWith('display_name:')) {
            currentModel.display_name = line.split(':').slice(1).join(':').trim();
          } else if (line.trim().startsWith('visible:')) {
            currentModel.visible = line.split(':').slice(1).join(':').trim() !== 'false';
          }
        }
        if (currentModel.model_name) {
          modelList.push(currentModel as ModelOption);
        }

        // Filter visible models
        const visibleModels = modelList.filter(m => m.visible !== false);
        setModels(visibleModels);

        // Set first model as default if current selection is invalid
        if (visibleModels.length > 0 && !visibleModels.find(m => m.model_name === selectedModel)) {
          onModelChange(visibleModels[0].model_name);
        }
      } catch (error) {
        console.error('Failed to load models from config, using defaults:', error);
        // Fallback to default models
        const defaultModels: ModelOption[] = [
          { model_name: 'claude-3-haiku', display_name: 'Claude 3 Haiku' },
          { model_name: 'claude-3-opus', display_name: 'Claude 3 Opus' },
          { model_name: 'gpt-4o', display_name: 'GPT-4o' },
          { model_name: 'gpt-4o-mini', display_name: 'GPT-4o Mini' },
          { model_name: 'gemini-1.5-pro', display_name: 'Gemini 1.5 Pro' },
          { model_name: 'gemini-1.5-flash', display_name: 'Gemini 1.5 Flash' },
        ];
        setModels(defaultModels);
      } finally {
        setLoading(false);
      }
    }

    loadModels();
  }, [selectedModel, onModelChange]);

  const handleChange = (event: SelectChangeEvent) => {
    onModelChange(event.target.value);
  };

  return (
    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
      <FormControl sx={{ minWidth: 250 }}>
        <InputLabel id="model-select-label">{t('select_model')}</InputLabel>
        <Select
          labelId="model-select-label"
          id="model-select"
          value={selectedModel}
          label={t('select_model')}
          onChange={handleChange}
          disabled={loading}
        >
          {loading ? (
            <MenuItem value="" disabled>
              <CircularProgress size={20} sx={{ mr: 1 }} />
              {t('checking_status')}
            </MenuItem>
          ) : (
            models.map((model) => (
              <MenuItem key={model.model_name} value={model.model_name}>
                {model.display_name || model.model_name}
              </MenuItem>
            ))
          )}
        </Select>
      </FormControl>

      <Button
        variant="outlined"
        color="error"
        startIcon={<DeleteOutlineIcon />}
        onClick={onClearChat}
      >
        {t('clear_chat')}
      </Button>
    </Box>
  );
}
