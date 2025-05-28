import React from "react";
import ReactDOM from "react-dom";
import App from "./App";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";


/**
 * Entry point with Material-UI ThemeProvider.
 * You can customize the theme for your brand colors.
 */
const theme = createTheme({
  palette: {
    primary: { main: "#1976d2" },
    // Add your color scheme here
  },
});

ReactDOM.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>,
  document.getElementById("root")
);