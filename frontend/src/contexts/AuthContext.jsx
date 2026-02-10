import React, { createContext, useState, useCallback, useEffect } from "react";

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initialize from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem("authToken");
    const storedUser = localStorage.getItem("authUser");
    
    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch (err) {
        console.error("Failed to restore auth from localStorage:", err);
        localStorage.removeItem("authToken");
        localStorage.removeItem("authUser");
      }
    }
    setLoading(false);
  }, []);

  const signup = useCallback(async (email, password, name = "") => {
    setLoading(true);
    setError(null);
    try {
      // Call backend signup endpoint (will be created after Cognito setup)
      const response = await fetch(`${process.env.REACT_APP_API_BASE}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.message || "Signup failed");
      }

      const data = await response.json();
      
      // Store token and user info
      localStorage.setItem("authToken", data.idToken);
      localStorage.setItem("authUser", JSON.stringify({
        userId: data.userId,
        email: data.email,
        name: data.name || "",
      }));

      setToken(data.idToken);
      setUser({
        userId: data.userId,
        email: data.email,
        name: data.name || "",
      });

      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      // Call backend login endpoint
      const response = await fetch(`${process.env.REACT_APP_API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.message || "Login failed");
      }

      const data = await response.json();
      
      // Store token and user info
      localStorage.setItem("authToken", data.idToken);
      localStorage.setItem("authUser", JSON.stringify({
        userId: data.userId,
        email: data.email,
        name: data.name || "",
      }));

      setToken(data.idToken);
      setUser({
        userId: data.userId,
        email: data.email,
        name: data.name || "",
      });

      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("authToken");
    localStorage.removeItem("authUser");
  }, []);

  const value = {
    user,
    token,
    loading,
    error,
    signup,
    login,
    logout,
    isAuthenticated: !!token,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
