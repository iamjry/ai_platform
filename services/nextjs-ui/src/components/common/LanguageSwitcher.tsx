/**
 * Language Switcher Component
 * Dropdown to switch between supported languages
 */

'use client';

import * as React from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import { useI18n, LANGUAGES } from '@/lib/i18n';

export function LanguageSwitcher() {
  const { language, setLanguage, t } = useI18n();

  const handleChange = (event: SelectChangeEvent) => {
    setLanguage(event.target.value as any);
  };

  return (
    <FormControl sx={{ minWidth: 150 }} size="small">
      <InputLabel id="language-select-label">{t('language')}</InputLabel>
      <Select
        labelId="language-select-label"
        id="language-select"
        value={language}
        label={t('language')}
        onChange={handleChange}
      >
        {Object.entries(LANGUAGES).map(([code, langInfo]) => (
          <MenuItem key={code} value={code}>
            {langInfo.nativeName}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
