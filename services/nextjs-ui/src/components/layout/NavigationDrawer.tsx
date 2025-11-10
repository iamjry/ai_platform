/**
 * Material Design 3 Navigation Drawer
 * Mobile navigation drawer
 */

'use client';

import * as React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Divider,
  Typography,
  Box,
} from '@mui/material';
import ChatIcon from '@mui/icons-material/Chat';
import StorageIcon from '@mui/icons-material/Storage';
import DescriptionIcon from '@mui/icons-material/Description';
import SettingsIcon from '@mui/icons-material/Settings';

const DRAWER_WIDTH = 280;

interface NavigationDrawerProps {
  open: boolean;
  onClose: () => void;
  activeRoute?: string;
  onNavigate?: (route: string) => void;
}

const navigationItems = [
  { id: 'chat', label: 'Chat', icon: <ChatIcon />, route: '/' },
  { id: 'sql', label: 'SQL', icon: <StorageIcon />, route: '/sql' },
  { id: 'documents', label: 'Documents', icon: <DescriptionIcon />, route: '/documents' },
  { id: 'settings', label: 'Settings', icon: <SettingsIcon />, route: '/settings' },
];

export function NavigationDrawer({ open, onClose, activeRoute = '/', onNavigate }: NavigationDrawerProps) {
  const handleNavigate = (route: string) => {
    onNavigate?.(route);
    onClose();
  };

  return (
    <Drawer
      open={open}
      onClose={onClose}
      sx={{
        display: { xs: 'block', sm: 'none' },
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
        },
      }}
    >
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          AI Platform
        </Typography>
      </Toolbar>
      <Divider />
      <List sx={{ pt: 2 }}>
        {navigationItems.map((item) => (
          <ListItem key={item.id} disablePadding>
            <ListItemButton
              selected={activeRoute === item.route}
              onClick={() => handleNavigate(item.route)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
}
