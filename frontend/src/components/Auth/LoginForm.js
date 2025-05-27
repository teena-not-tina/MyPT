import React, { useState } from "react";
import { Box, TextField, Button, Alert } from "@mui/material";
import axios from "axios";

/**
 * LoginForm handles username/password login.
 * Calls FastAPI backend (e.g., /auth/login).
 * On success, redirect to main page. (replace with chatbot page later)
 */
export default function LoginForm({ onSuccess }) {
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");

  // Replace with your backend endpoint
  const apiUrl = `${process.env.REACT_APP_API_BASE_URL || ""}/auth/login`;

  const handleChange = (e) => {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const res = await axios.post(apiUrl, form, { withCredentials: true });
      // Save token/user info as needed
      localStorage.setItem("user", JSON.stringify(res.data));
      // TODO: Use context or state for user info
      onSuccess();
      // Redirect to main page (replace with chatbot route in future)
      window.location.href = "/main";
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "로그인에 실패했습니다. 아이디와 비밀번호를 확인하세요."
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
        로그인
      </Button>
    </Box>
  );
}