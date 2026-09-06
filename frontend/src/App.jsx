import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import AILogging from './pages/AILogging'
import History from './pages/History'
import Coach from './pages/Coach'
import Settings from './pages/Settings'
import NotFound from './pages/NotFound'
import './index.css'

function Protected({ children }) {
  const { token, loading } = useAuth()
  if (loading) return <div className="loading-fill"><div className="spinner spinner--dark" /></div>
  if (!token) return <Navigate to="/login" replace />
  return children
}

function Guest({ children }) {
  const { token, loading } = useAuth()
  if (loading) return <div className="loading-fill"><div className="spinner spinner--dark" /></div>
  if (token) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Guest><Login /></Guest>} />
          <Route path="/register" element={<Guest><Register /></Guest>} />
          <Route element={<Protected><Layout /></Protected>}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/log" element={<AILogging />} />
            <Route path="/history" element={<History />} />
            <Route path="/coach" element={<Coach />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}