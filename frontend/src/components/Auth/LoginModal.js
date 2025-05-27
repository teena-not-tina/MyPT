import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Tabs,
  Tab,
  Box,
  IconButton,
  Typography
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import LoginForm from "./LoginForm";
import RegisterForm from "./RegisterForm";
import SocialLoginButtons from "./SocialLoginButtons";

/**
 * Modal for login/register.
 * Tabbed interface for switching between login/register.
 * Social logins shown at top if available.
 */
export default function LoginModal({ open, onClose }) {
  const [tab, setTab] = useState(0);

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <Box sx={{ display: "flex", justifyContent: "flex-end", p: 1 }}>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </Box>
      <DialogTitle sx={{ pt: 0, textAlign: "center" }}>
        {tab === 0 ? "로그인" : "회원가입"}
      </DialogTitle>
      <DialogContent>
        {/* Social Login Buttons */}
        <SocialLoginButtons />
        <Tabs
          value={tab}
          onChange={(_, v) => setTab(v)}
          centered
          sx={{ mb: 2, mt: 2 }}
        >
          <Tab label="로그인" />
          <Tab label="회원가입" />
        </Tabs>
        {tab === 0 ? (
          <LoginForm onSuccess={onClose} />
        ) : (
          <RegisterForm onSuccess={() => setTab(0)} />
        )}
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary" align="center" display="block">
            {/* Guidance for future: add privacy links, help, etc. */}
          </Typography>
        </Box>
      </DialogContent>
    </Dialog>
  );
}