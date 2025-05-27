import React from "react";
import { Container, Typography, Box } from "@mui/material";

/**
 * MainPage shown after login.
 * TODO: Change this to Chatbot page in future.
 */
export default function MainPage() {
  return (
    <Container maxWidth="md" sx={{ minHeight: "100vh", py: 5 }}>
      <Box sx={{ textAlign: "center", mt: 10 }}>
        <Typography variant="h4">메인 페이지</Typography>
        <Typography variant="body1" sx={{ mt: 2 }}>
          로그인 성공! (여기서 챗봇 페이지로 이동하도록 변경 예정)
        </Typography>
      </Box>
    </Container>
  );
}