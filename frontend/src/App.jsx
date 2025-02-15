import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import Login from "./components/Login";
import Signup from "./components/Signup";
import Dashboard from "./components/Dashboard";
import History from "./components/History";
// import History from './components/History/index.js';

import LandingPage from "./components/LandingPage";
import About from "./components/About";
import ContactForm from "./components/ContactForm";
import ProtectedRoute from "./components/ProtectedRoute";
import Footer from "./components/Footer";
import "./App.css";
import AnimatedBackground from "./components/AnimatedBackground";

const App = () => {
  return (
    <Router>
      <AuthProvider>
        <div className="app">
          <AnimatedBackground />
          <Navbar />
          <main className="main-content">
            {
              <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/about" element={<About />} />
                <Route path="/contact" element={<ContactForm />} />
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<Signup />} />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/history"
                  element={
                    <ProtectedRoute>
                      <History />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            }
          </main>
          <Footer />
        </div>
      </AuthProvider>
    </Router>
  );
};

export default App;
