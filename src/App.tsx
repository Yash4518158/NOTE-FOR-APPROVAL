import React, { useState, useEffect } from 'react';
import type { User } from './types';
import { LoginView } from './components/LoginView';
import { DashboardHeader } from './components/DashboardHeader';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const savedUser = localStorage.getItem('nfa_user');
    const savedToken = localStorage.getItem('nfa_token');
    if (savedUser && savedToken) {
      try {
        setUser(JSON.parse(savedUser));
        setToken(savedToken);
      } catch (e) {
        localStorage.removeItem('nfa_user');
        localStorage.removeItem('nfa_token');
      }
    }
  }, []);

  const handleLoginSuccess = (loggedInUser: User, authToken: string) => {
    setUser(loggedInUser);
    setToken(authToken);
    localStorage.setItem('nfa_user', JSON.stringify(loggedInUser));
    localStorage.setItem('nfa_token', authToken);
  };

  const handleLogout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('nfa_user');
    localStorage.removeItem('nfa_token');
  };

  return (
    <div>
      {user && token ? (
        <DashboardHeader user={user} onLogout={handleLogout} />
      ) : (
        <LoginView onLoginSuccess={handleLoginSuccess} />
      )}
    </div>
  );
};

export default App;
