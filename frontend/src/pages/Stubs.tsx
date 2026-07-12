import React from 'react';
import { Card } from '../components/ui';

const PageStub: React.FC<{ title: string; agent?: string }> = ({ title, agent }) => (
  <div className="max-w-6xl mx-auto">
    <Card padding="lg">
      <h1 className="text-3xl font-bold mb-4">{title}</h1>
      <p className="text-neutral-600 mb-6">{agent ? `Being built by ${agent}` : 'Page coming soon'}</p>
    </Card>
  </div>
);

export const NotFoundPage: React.FC = () => (
  <PageStub title="Page Not Found" />
);
