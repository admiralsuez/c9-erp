import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Textarea } from '../components/ui/Textarea';
import { Card, CardHeader, CardBody, CardFooter } from '../components/ui/Card';
import { Badge, StatusBadge } from '../components/ui/Badge';
import { StatCard } from '../components/common/StatCard';
import { EntityListCard } from '../components/common/EntityListCard';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { AuthContext } from '../context/AuthContext';
import { MemoryRouter } from 'react-router-dom';

describe('Input', () => {
  it('renders with label and input', () => {
    render(<Input label="Email" placeholder="Enter email" />);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter email')).toBeInTheDocument();
  });

  it('shows error message with aria-invalid', () => {
    render(<Input label="Email" error="Required" />);
    expect(screen.getByRole('alert')).toHaveTextContent('Required');
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true');
  });

  it('shows hint text', () => {
    render(<Input label="Email" hint="Enter a valid email" />);
    expect(screen.getByText('Enter a valid email')).toBeInTheDocument();
  });

  it('disables the input', () => {
    render(<Input label="Email" disabled />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });

  it('fires onChange handler', () => {
    const handleChange = vi.fn();
    render(<Input label="Name" onChange={handleChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'test' } });
    expect(handleChange).toHaveBeenCalled();
  });
});

describe('Select', () => {
  const options = [
    { value: '', label: 'Select...' },
    { value: 'apple', label: 'Apple' },
    { value: 'banana', label: 'Banana' },
  ];

  it('renders with label and options', () => {
    render(<Select label="Fruit" options={options} />);
    expect(screen.getByLabelText('Fruit')).toBeInTheDocument();
    expect(screen.getByText('Apple')).toBeInTheDocument();
    expect(screen.getByText('Banana')).toBeInTheDocument();
  });

  it('shows error with aria-invalid', () => {
    render(<Select label="Fruit" options={options} error="Pick one" />);
    expect(screen.getByRole('alert')).toHaveTextContent('Pick one');
    expect(screen.getByRole('combobox')).toHaveAttribute('aria-invalid', 'true');
  });

  it('renders placeholder as first disabled option', () => {
    render(<Select label="Fruit" options={options} placeholder="Choose..." />);
    const firstOption = screen.getByText('Choose...');
    expect(firstOption).toBeInTheDocument();
  });
});

describe('Textarea', () => {
  it('renders with label', () => {
    render(<Textarea label="Notes" placeholder="Enter notes" />);
    expect(screen.getByLabelText('Notes')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter notes')).toBeInTheDocument();
  });

  it('shows error message', () => {
    render(<Textarea label="Notes" error="Required" />);
    expect(screen.getByRole('alert')).toHaveTextContent('Required');
  });

  it('fires onChange handler', () => {
    const handleChange = vi.fn();
    render(<Textarea label="Notes" onChange={handleChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'hello' } });
    expect(handleChange).toHaveBeenCalled();
  });
});

describe('Card', () => {
  it('renders Card with children', () => {
    render(<Card>Content</Card>);
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('renders CardHeader', () => {
    render(<CardHeader>Header</CardHeader>);
    expect(screen.getByText('Header')).toBeInTheDocument();
  });

  it('renders CardBody', () => {
    render(<CardBody>Body</CardBody>);
    expect(screen.getByText('Body')).toBeInTheDocument();
  });

  it('renders CardFooter', () => {
    render(<CardFooter>Footer</CardFooter>);
    expect(screen.getByText('Footer')).toBeInTheDocument();
  });
});

describe('Badge', () => {
  it('renders with default variant', () => {
    render(<Badge>Default</Badge>);
    expect(screen.getByText('Default')).toBeInTheDocument();
  });

  it('renders with different variants', () => {
    const { rerender } = render(<Badge variant="success">OK</Badge>);
    expect(screen.getByText('OK')).toBeInTheDocument();
    rerender(<Badge variant="error">Fail</Badge>);
    expect(screen.getByText('Fail')).toBeInTheDocument();
    rerender(<Badge variant="warning">Warn</Badge>);
    expect(screen.getByText('Warn')).toBeInTheDocument();
  });
});

describe('StatusBadge', () => {
  it('renders raw status text', () => {
    const { rerender } = render(<StatusBadge status="draft" />);
    expect(screen.getByText('draft')).toBeInTheDocument();
    rerender(<StatusBadge status="approved" />);
    expect(screen.getByText('approved')).toBeInTheDocument();
    rerender(<StatusBadge status="delivered" />);
    expect(screen.getByText('delivered')).toBeInTheDocument();
  });

  it('falls back for unknown status', () => {
    render(<StatusBadge status="some_status" />);
    expect(screen.getByText('some_status')).toBeInTheDocument();
  });
});

describe('StatCard', () => {
  it('renders label and value', () => {
    render(<StatCard label="Orders" value={42} />);
    expect(screen.getByText('Orders')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('renders trend indicator', () => {
    render(<StatCard label="Sales" value={100} trend="up" trendValue="+12%" />);
    expect(screen.getByText('+12%')).toBeInTheDocument();
  });

  it('fires onClick handler', () => {
    const handleClick = vi.fn();
    render(<StatCard label="Users" value={5} onClick={handleClick} />);
    fireEvent.click(screen.getByText('Users').closest('div')!);
    expect(handleClick).toHaveBeenCalledOnce();
  });
});

describe('EntityListCard', () => {
  it('renders title and subtitle', () => {
    render(<EntityListCard title="Test Title" subtitle="Sub" />);
    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Sub')).toBeInTheDocument();
  });

  it('renders description', () => {
    render(<EntityListCard title="T" description="Desc" />);
    expect(screen.getByText('Desc')).toBeInTheDocument();
  });

  it('fires onClick handler', () => {
    const handleClick = vi.fn();
    render(<EntityListCard title="Clickable" onClick={handleClick} />);
    fireEvent.click(screen.getByText('Clickable'));
    expect(handleClick).toHaveBeenCalledOnce();
  });
});

describe('ProtectedRoute', () => {
  it('shows spinner when loading', () => {
    render(
      <AuthContext.Provider value={{ user: null, isAuthenticated: false, isLoading: true, login: vi.fn(), logout: vi.fn(), setUser: vi.fn() }}>
        <ProtectedRoute><div>Protected</div></ProtectedRoute>
      </AuthContext.Provider>
    );
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('redirects to login when unauthenticated', () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={{ user: null, isAuthenticated: false, isLoading: false, login: vi.fn(), logout: vi.fn(), setUser: vi.fn() }}>
          <ProtectedRoute><div>Protected</div></ProtectedRoute>
        </AuthContext.Provider>
      </MemoryRouter>
    );
    expect(screen.queryByText('Protected')).not.toBeInTheDocument();
  });

  it('renders children when authenticated', () => {
    const mockUser = { id: 1, full_name: 'Test', email: 'test@test.com', role: { id: 1, name: 'Admin', permissions: [] }, is_active: true, created_at: '2024-01-01', updated_at: '2024-01-01' } as any;
    render(
      <MemoryRouter>
        <AuthContext.Provider value={{ user: mockUser, isAuthenticated: true, isLoading: false, login: vi.fn(), logout: vi.fn(), setUser: vi.fn() }}>
          <ProtectedRoute><div>Protected</div></ProtectedRoute>
        </AuthContext.Provider>
      </MemoryRouter>
    );
    expect(screen.getByText('Protected')).toBeInTheDocument();
  });
});

describe('ErrorBoundary', () => {
  it('catches errors and shows fallback', () => {
    const ThrowingComponent = () => { throw new Error('Test error'); };
    const origError = console.error;
    console.error = vi.fn();
    try {
      render(
        <ErrorBoundary><ThrowingComponent /></ErrorBoundary>
      );
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.getByText('Test error')).toBeInTheDocument();
    } finally {
      console.error = origError;
    }
  });
});
