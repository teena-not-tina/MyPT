import React, { useState } from "react";
import { Box, TextField, Button, Alert } from "@mui/material";
import axios from "axios";

/**
 * RegisterForm handles new user registration.
 * Calls FastAPI backend (e.g., /auth/register).
 * On success, switches to login tab.
 */
export default function RegisterForm({ onSuccess }) {
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  // Replace with your backend endpoint
  const apiUrl = `${process.env.REACT_APP_API_BASE_URL || ""}/auth/register`;

  const handleChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await axios.post(apiUrl, form);
      // Optionally, auto-login or switch to login tab
      onSuccess();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "회원가입에 실패했습니다. 정보를 다시 확인하세요."
      );
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <TextField
        label="아이디"
        name="username"
        value={form.username}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
      />
      <TextField
        label="비밀번호"
        name="password"
        type="password"
        value={form.password}
        onChange={handleChange}
        fullWidth
        margin="normal"
        required
      />
      {error && <Alert severity="error">{error}</Alert>}
      <Button
        type="submit"
        fullWidth
        variant="contained"
        sx={{ mt: 2 }}
      >
        회원가입
      </Button>
    </Box>
  );
}