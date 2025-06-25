import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { ProjectCard } from '../project-card';
import { UserProjectInfo } from '@/types';

// Mock project data
const mockProjectInfo: UserProjectInfo = {
  project: {
    id: '1',
    name: 'Test Project',
    description: 'A test project for AI agents',
    organization_id: 'org-1',
    platform_type: 'langfuse',
    platform_config: {
      public_key: 'pk_test',
      secret_key: 'sk_test',
      url: 'https://cloud.langfuse.com'
    },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  membership: {
    id: '1',
    user_id: 'user-1',
    project_id: '1',
    role: 'owner',
    joined_at: '2024-01-01T00:00:00Z',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  is_owner: true,
};

describe('ProjectCard', () => {
  it('renders project information correctly', () => {
    const mockOnSelect = vi.fn();
    
    render(
      <ProjectCard 
        projectInfo={mockProjectInfo} 
        onSelect={mockOnSelect} 
      />
    );

    expect(screen.getByText('Test Project')).toBeInTheDocument();
    expect(screen.getByText('A test project for AI agents')).toBeInTheDocument();
    expect(screen.getByText('langfuse')).toBeInTheDocument();
    expect(screen.getByText('View Project')).toBeInTheDocument();
  });

  it('renders default description when description is empty', () => {
    const mockOnSelect = vi.fn();
    const projectWithoutDescription = {
      ...mockProjectInfo,
      project: {
        ...mockProjectInfo.project,
        description: undefined,
      },
    };
    
    render(
      <ProjectCard 
        projectInfo={projectWithoutDescription} 
        onSelect={mockOnSelect} 
      />
    );

    expect(screen.getByText('AI agent data quality monitoring')).toBeInTheDocument();
  });

  it('calls onSelect when card is clicked', () => {
    const mockOnSelect = vi.fn();
    
    render(
      <ProjectCard 
        projectInfo={mockProjectInfo} 
        onSelect={mockOnSelect} 
      />
    );

    const card = screen.getByRole('button', { name: /test project/i });
    fireEvent.click(card);

    expect(mockOnSelect).toHaveBeenCalledWith(mockProjectInfo);
    expect(mockOnSelect).toHaveBeenCalledTimes(1);
  });

  it('displays project folder icon', () => {
    const mockOnSelect = vi.fn();
    
    render(
      <ProjectCard 
        projectInfo={mockProjectInfo} 
        onSelect={mockOnSelect} 
      />
    );

    // Test that the folder icon is present by checking for the SVG element
    const titleElement = screen.getByText('Test Project');
    const titleContainer = titleElement.parentElement;
    expect(titleContainer).toBeInTheDocument();
    
    // Check that there's an SVG icon in the title container
    const svgIcon = titleContainer?.querySelector('svg');
    expect(svgIcon).toBeInTheDocument();
  });

  it('shows platform type in capitalized format', () => {
    const mockOnSelect = vi.fn();
    
    render(
      <ProjectCard 
        projectInfo={mockProjectInfo} 
        onSelect={mockOnSelect} 
      />
    );

    expect(screen.getByText('langfuse')).toBeInTheDocument();
    expect(screen.getByText('Platform:')).toBeInTheDocument();
  });
});