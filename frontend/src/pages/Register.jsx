import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const Register = ({ setIsAuthenticated, setUser }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await res.json();
      if (res.ok) {
        setIsAuthenticated(true);
        setUser(data.user);
        navigate('/dashboard');
      } else {
        setError(data.error || 'Registration failed');
      }
    } catch {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field) => (e) =>
    setFormData(prev => ({ ...prev, [field]: e.target.value }));

  return (
    <div className="min-h-screen flex items-center justify-center bg-light p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-card w-full max-w-md p-8"
      >
        <div className="text-center mb-8">
          <div className="font-bold text-2xl tracking-tighter text-dark mb-1">
            Finora<span className="text-primary">.</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-dark mb-2">Create Account</h1>
          <p className="text-dark/60">Start managing your finances and wardrobe.</p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-500 p-3 rounded-lg mb-6 text-sm font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-dark/80 mb-2">Full Name</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={handleChange('name')}
              className="w-full px-4 py-3 rounded-xl border border-secondary/50 bg-white/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-dark"
              placeholder="Adrian"
              disabled={loading}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-dark/80 mb-2">Email Address</label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={handleChange('email')}
              className="w-full px-4 py-3 rounded-xl border border-secondary/50 bg-white/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-dark"
              placeholder="you@example.com"
              disabled={loading}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-dark/80 mb-2">Password</label>
            <input
              type="password"
              required
              minLength="6"
              value={formData.password}
              onChange={handleChange('password')}
              className="w-full px-4 py-3 rounded-xl border border-secondary/50 bg-white/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-dark"
              placeholder="At least 6 characters"
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-dark text-white font-medium rounded-xl hover:bg-dark/90 transition-all active:scale-[0.98] shadow-lg shadow-dark/20 mt-2 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className="text-center mt-8 text-dark/60 text-sm">
          Already have an account?{' '}
          <Link to="/login" className="text-dark font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  );
};

export default Register;