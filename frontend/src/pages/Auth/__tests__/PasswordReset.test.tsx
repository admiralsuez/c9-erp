import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import PasswordReset from '../PasswordReset';
import ForgotPassword from '../ForgotPassword';
import * as authApi from '../../../api/auth';

vi.mock('../../../api/auth');

const renderWithRouter = (component: React.ReactNode) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('ForgotPassword Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders forgot password form', () => {
    renderWithRouter(<ForgotPassword />);
    
    expect(screen.getByText('Forgot Password?')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('your@email.com')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Send Reset Link/i })).toBeInTheDocument();
  });

  test('submits email and shows success message', async () => {
    vi.mocked(authApi.requestPasswordReset).mockResolvedValue({});
    
    renderWithRouter(<ForgotPassword />);
    
    const emailInput = screen.getByPlaceholderText('your@email.com');
    const submitButton = screen.getByRole('button', { name: /Send Reset Link/i });
    
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Email Sent')).toBeInTheDocument();
    });
    
    expect(authApi.requestPasswordReset).toHaveBeenCalledWith({
      email: 'test@example.com'
    });
  });

  test('shows error on request failure', async () => {
    const errorMessage = 'Failed to send email';
    vi.mocked(authApi.requestPasswordReset).mockRejectedValue({
      response: { data: { detail: errorMessage } }
    });
    
    renderWithRouter(<ForgotPassword />);
    
    const emailInput = screen.getByPlaceholderText('your@email.com');
    const submitButton = screen.getByRole('button', { name: /Send Reset Link/i });
    
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  test('disables submit button when email is empty', () => {
    renderWithRouter(<ForgotPassword />);
    
    const submitButton = screen.getByRole('button', { name: /Send Reset Link/i });
    expect(submitButton).toBeDisabled();
  });
});

describe('PasswordReset Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.replaceState({}, '', '/reset-password?token=test-token-123');
  });

  test('renders password reset form', () => {
    renderWithRouter(<PasswordReset />);
    
    expect(screen.getByText('Reset Password')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter new password')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Confirm new password')).toBeInTheDocument();
  });

  test('shows invalid link message when no token', () => {
    window.history.replaceState({}, '', '/reset-password');
    
    renderWithRouter(<PasswordReset />);
    
    expect(screen.getByText('Invalid Link')).toBeInTheDocument();
    expect(screen.getByText(/This password reset link is invalid/)).toBeInTheDocument();
  });

  test('toggles password visibility', () => {
    renderWithRouter(<PasswordReset />);
    
    const passwordInput = screen.getByPlaceholderText('Enter new password') as HTMLInputElement;
    const toggleButtons = screen.getAllByRole('button');
    const passwordToggle = toggleButtons.find(btn => btn.className.includes('absolute'));
    
    expect(passwordInput.type).toBe('password');
    
    if (passwordToggle) {
      fireEvent.click(passwordToggle);
      expect(passwordInput.type).toBe('text');
      
      fireEvent.click(passwordToggle);
      expect(passwordInput.type).toBe('password');
    }
  });

  test('shows password strength requirements', async () => {
    renderWithRouter(<PasswordReset />);
    
    const passwordInput = screen.getByPlaceholderText('Enter new password');
    
    fireEvent.change(passwordInput, { target: { value: 'Weak1' } });
    
    await waitFor(() => {
      expect(screen.getByText('At least 8 characters')).toBeInTheDocument();
    });
  });

  test('validates password requirements', async () => {
    renderWithRouter(<PasswordReset />);
    
    const passwordInput = screen.getByPlaceholderText('Enter new password');
    
    // Test each requirement
    const requirements = [
      { password: 'short', requirement: 'At least 8 characters' },
      { password: 'nouppercase123', requirement: 'One uppercase letter' },
      { password: 'NOLOWERCASE123', requirement: 'One lowercase letter' },
      { password: 'NoNumbers', requirement: 'One number' },
    ];
    
    for (const { password, requirement } of requirements) {
      fireEvent.change(passwordInput, { target: { value: password } });
      
      await waitFor(() => {
        const elem = screen.getByText(requirement);
        expect(elem.parentElement?.className).not.toContain('text-green');
      });
    }
  });

  test('validates password confirmation match', async () => {
    renderWithRouter(<PasswordReset />);
    
    const passwordInput = screen.getByPlaceholderText('Enter new password');
    const confirmInput = screen.getByPlaceholderText('Confirm new password');
    
    fireEvent.change(passwordInput, { target: { value: 'ValidPassword123' } });
    fireEvent.change(confirmInput, { target: { value: 'DifferentPassword123' } });
    
    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    });
  });

  test('disables submit button until passwords match and are valid', async () => {
    renderWithRouter(<PasswordReset />);
    
    const submitButton = screen.getByRole('button', { name: /Reset Password/i });
    expect(submitButton).toBeDisabled();
    
    const passwordInput = screen.getByPlaceholderText('Enter new password');
    const confirmInput = screen.getByPlaceholderText('Confirm new password');
    
    fireEvent.change(passwordInput, { target: { value: 'ValidPassword123' } });
    fireEvent.change(confirmInput, { target: { value: 'ValidPassword123' } });
    
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });
  });

  test('submits password reset and shows success', async () => {
    vi.mocked(authApi.resetPassword).mockResolvedValue({});
    
    renderWithRouter(<PasswordReset />);
    
    const passwordInput = screen.getByPlaceholderText('Enter new password');
    const confirmInput = screen.getByPlaceholderText('Confirm new password');
    const submitButton = screen.getByRole('button', { name: /Reset Password/i });
    
    fireEvent.change(passwordInput, { target: { value: 'ValidPassword123' } });
    fireEvent.change(confirmInput, { target: { value: 'ValidPassword123' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Password Updated')).toBeInTheDocument();
    });
    
    expect(authApi.resetPassword).toHaveBeenCalledWith({
      token: 'test-token-123',
      new_password: 'ValidPassword123'
    });
  });

  test('shows error on reset failure', async () => {
    const errorMessage = 'Invalid or expired token';
    vi.mocked(authApi.resetPassword).mockRejectedValue({
      response: { data: { detail: errorMessage } }
    });
    
    renderWithRouter(<PasswordReset />);
    
    const passwordInput = screen.getByPlaceholderText('Enter new password');
    const confirmInput = screen.getByPlaceholderText('Confirm new password');
    const submitButton = screen.getByRole('button', { name: /Reset Password/i });
    
    fireEvent.change(passwordInput, { target: { value: 'ValidPassword123' } });
    fireEvent.change(confirmInput, { target: { value: 'ValidPassword123' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  test('can navigate back to login', () => {
    renderWithRouter(<PasswordReset />);
    
    const loginButtons = screen.getAllByText(/Back to Login/);
    expect(loginButtons.length).toBeGreaterThan(0);
  });
});
