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
  useTheme,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

interface AppBarProps {
  onMenuClick: () => void;
}

export function AppBar({ onMenuClick }: AppBarProps) {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleThemeToggle = () => {
    // TODO: Implement theme toggle
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
          AI Platform
        </Typography>

        {/* Spacer */}
        <Box sx={{ flexGrow: 1 }} />

        {/* Theme toggle button */}
        <IconButton color="inherit" onClick={handleThemeToggle} sx={{ mr: 1 }}>
          {theme.palette.mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
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
            {theme.palette.mode === 'dark' ? 'Light Mode' : 'Dark Mode'}
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>Settings</MenuItem>
          <MenuItem onClick={handleMenuClose}>About</MenuItem>
        </Menu>
      </Toolbar>
    </MuiAppBar>
  );
}
