/**
 * Material Design 3 Navigation Rail
 * Side navigation for desktop/tablet
 */

'use client';

import * as React from 'react';
import { Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Toolbar } from '@mui/material';
import ChatIcon from '@mui/icons-material/Chat';
import StorageIcon from '@mui/icons-material/Storage';
import DescriptionIcon from '@mui/icons-material/Description';
import SettingsIcon from '@mui/icons-material/Settings';

const DRAWER_WIDTH = 80;

interface NavigationRailProps {
  activeRoute?: string;
  onNavigate?: (route: string) => void;
}

const navigationItems = [
  { id: 'chat', label: 'Chat', icon: <ChatIcon />, route: '/' },
  { id: 'sql', label: 'SQL', icon: <StorageIcon />, route: '/sql' },
  { id: 'documents', label: 'Documents', icon: <DescriptionIcon />, route: '/documents' },
  { id: 'settings', label: 'Settings', icon: <SettingsIcon />, route: '/settings' },
];

export function NavigationRail({ activeRoute = '/', onNavigate }: NavigationRailProps) {
  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        display: { xs: 'none', sm: 'block' },
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
        },
      }}
    >
      <Toolbar />
      <List sx={{ pt: 2 }}>
        {navigationItems.map((item) => (
          <ListItem key={item.id} disablePadding sx={{ mb: 1 }}>
            <ListItemButton
              selected={activeRoute === item.route}
              onClick={() => onNavigate?.(item.route)}
              sx={{
                flexDirection: 'column',
                py: 2,
                '&.Mui-selected': {
                  backgroundColor: 'rgba(103, 80, 164, 0.12)',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 'auto', mb: 0.5 }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{
                  variant: 'caption',
                  align: 'center',
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
}
