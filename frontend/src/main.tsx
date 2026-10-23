import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { WalletProviderTree } from "./lib/wallet-context";
import { ToastProvider } from "./lib/toast-context";
import "./styles/tokens.css";
import "./styles/global.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ToastProvider>
        <WalletProviderTree>
          <App />
        </WalletProviderTree>
      </ToastProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
