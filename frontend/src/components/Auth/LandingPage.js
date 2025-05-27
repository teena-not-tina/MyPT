import React from "react";
import { Button, Container, Typography, Box } from "@mui/material";
import LoginModal from "./LoginModal";

/**
 * LandingPage displays the app logo/title and a login button/modal.
 * Responsive for mobile and desktop.
 * You can later add more intro text or branding here.
 */
export default function LandingPage() {
  const [open, setOpen] = React.useState(false);

  return (
    <Container
      maxWidth="sm"
      sx={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* App Title/Logo */}
      <Typography variant="h3" align="center" sx={{ mb: 2 }}>
        B-FIT
      </Typography>
      <Typography variant="h6" align="center" sx={{ mb: 5, color: "text.secondary" }}>
        AI Personal Trainer
      </Typography>
      {/* Login Button */}
      <Button
        size="large"
        variant="contained"
        color="primary"
        onClick={() => setOpen(true)}
        sx={{ px: 5, borderRadius: 2 }}
      >
        로그인 / 회원가입
      </Button>
      {/* Login/Register Modal */}
      <LoginModal open={open} onClose={() => setOpen(false)} />
    </Container>
  );
}