/**
 * Material Design 3 Top App Bar
 * Main navigation bar for the application
 */

'use client';

import * as React from 'react';
import {
  AppBar as MuiAppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Menu,
  MenuItem,
  useTheme as useMuiTheme,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import { useTheme } from '@/lib/theme/ThemeContext';
import { useI18n } from '@/lib/i18n';
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher';

interface AppBarProps {
  onMenuClick: () => void;
}

export function AppBar({ onMenuClick }: AppBarProps) {
  const muiTheme = useMuiTheme();
  const { mode, toggleTheme } = useTheme();
  const { t } = useI18n();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleThemeToggle = () => {
    toggleTheme();
    handleMenuClose();
  };

  return (
    <MuiAppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar>
        {/* Menu button for mobile */}
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={onMenuClick}
          sx={{
            mr: 2,
            display: { sm: 'none' },
          }}
        >
          <MenuIcon />
        </IconButton>

        {/* App title */}
        <Typography variant="h6" component="div" sx={{ flexGrow: 0, mr: 4 }}>
          {t('main_header')}
        </Typography>

        {/* Spacer */}
        <Box sx={{ flexGrow: 1 }} />

        {/* Language switcher */}
        <Box sx={{ mr: 2, display: { xs: 'none', sm: 'block' } }}>
          <LanguageSwitcher />
        </Box>

        {/* Theme toggle button */}
        <IconButton color="inherit" onClick={toggleTheme} sx={{ mr: 1 }}>
          {mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
        </IconButton>

        {/* More options menu */}
        <IconButton
          color="inherit"
          aria-label="more options"
          aria-controls="app-menu"
          aria-haspopup="true"
          onClick={handleMenuOpen}
        >
          <MoreVertIcon />
        </IconButton>

        <Menu
          id="app-menu"
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleThemeToggle}>
            {mode === 'dark' ? t('settings') + ' - ' + '淺色模式' : t('settings') + ' - ' + '深色模式'}
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>{t('settings')}</MenuItem>
          <MenuItem onClick={handleMenuClose}>{t('tab_about')}</MenuItem>
        </Menu>
      </Toolbar>
    </MuiAppBar>
  );
}
