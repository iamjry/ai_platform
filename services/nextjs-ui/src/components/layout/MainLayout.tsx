/**
 * Main Layout Component
 * Combines AppBar, NavigationRail, and NavigationDrawer
 */

'use client';

import * as React from 'react';
import { Box, Toolbar } from '@mui/material';
import { AppBar } from './AppBar';
import { NavigationRail } from './NavigationRail';
import { NavigationDrawer } from './NavigationDrawer';
import { usePathname, useRouter } from 'next/navigation';

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const pathname = usePathname();
  const router = useRouter();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleNavigate = (route: string) => {
    router.push(route);
  };

  return (
    <Box sx={{ display: 'flex' }}>
      {/* Top App Bar */}
      <AppBar onMenuClick={handleDrawerToggle} />

      {/* Navigation Rail (Desktop) */}
      <NavigationRail activeRoute={pathname} onNavigate={handleNavigate} />

      {/* Navigation Drawer (Mobile) */}
      <NavigationDrawer
        open={mobileOpen}
        onClose={handleDrawerToggle}
        activeRoute={pathname}
        onNavigate={handleNavigate}
      />

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - 80px)` },
          minHeight: '100vh',
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}
