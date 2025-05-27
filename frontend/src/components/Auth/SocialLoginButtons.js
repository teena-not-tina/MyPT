import React from "react";
import { Stack, Button } from "@mui/material";
import GoogleIcon from "@mui/icons-material/Google";

/**
 * SocialLoginButtons renders buttons for social login.
 * On click, redirects to backend FastAPI OAuth endpoints.
 * Add/remove providers as needed.
 */
export default function SocialLoginButtons() {
  // TODO: Replace with your backend's real OAuth endpoints.
  const providers = [
    {
      name: "Google",
      url: `${process.env.REACT_APP_API_BASE_URL || ""}/auth/google/login`,
      icon: <GoogleIcon />,
    },
    // Add Kakao, Naver, etc. as needed.
  ];

  return (
    <Stack spacing={1} sx={{ mb: 2 }}>
      {providers.map((p) => (
        <Button
          key={p.name}
          variant="outlined"
          fullWidth
          startIcon={p.icon}
          onClick={() => (window.location.href = p.url)}
        >
          {p.name}로 계속하기
        </Button>
      ))}
    </Stack>
  );
}