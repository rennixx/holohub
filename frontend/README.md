# HoloHub Frontend

Modern, production-grade admin dashboard for HoloHub - a spatial computing CMS for managing holographic displays at scale.

## Tech Stack

| Category | Technology | Purpose |
|----------|------------|---------|
| **Framework** | Next.js 14 | App Router, Server Components, RSC |
| **UI Library** | shadcn/ui | Accessible, customizable components |
| **Styling** | Tailwind CSS | Utility-first CSS framework |
| **3D Rendering** | React Three Fiber | WebGL-based GLB/GLTF viewer |
| **3D Loaders** | @react-three/drei | GLTFLoader, OrbitControls, environment |
| **State Management** | Zustand | Lightweight global state |
| **Data Fetching** | TanStack Query (React Query) | Server state management |
| **Forms** | React Hook Form + Zod | Form validation |
| **HTTP Client** | axios | API requests with interceptors |
| **Date/Time** | date-fns | Date formatting |
| **Icons** | Lucide React | Icon library |
| **Notifications** | Sonner (shadcn) | Toast notifications |
| **Deployment** | Vercel | Edge deployment with preview deployments |

## Project Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth route group
│   │   ├── login/
│   │   │   └── page.tsx          # Login page
│   │   ├── register/
│   │   │   └── page.tsx          # Registration page
│   │   └── layout.tsx            # Auth layout
│   │
│   ├── (dashboard)/              # Dashboard route group
│   │   ├── dashboard/
│   │   │   └── page.tsx          # Dashboard overview
│   │   ├── assets/
│   │   │   ├── page.tsx          # Assets library list
│   │   │   ├── [id]/
│   │   │   │   └── page.tsx      # Asset detail with 3D preview
│   │   │   └── upload/
│   │   │       └── page.tsx      # Asset upload page
│   │   ├── devices/
│   │   │   ├── page.tsx          # Device fleet table
│   │   │   └── [id]/
│   │   │       └── page.tsx      # Device detail page
│   │   ├── playlists/
│   │   │   ├── page.tsx          # Playlists list
│   │   │   ├── [id]/
│   │   │   │   └── page.tsx      # Playlist detail
│   │   │   └── new/
│   │   │       └── page.tsx      # Create playlist
│   │   ├── settings/
│   │   │   ├── page.tsx          # General settings
│   │   │   └── team/
│   │   │       └── page.tsx      # Team management
│   │   └── layout.tsx            # Dashboard layout
│   │
│   ├── globals.css               # Global styles
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Root redirect
│   ├── error.tsx                 # Error boundary
│   └── not-found.tsx             # 404 page
│
├── components/                   # React components
│   ├── auth/                     # Auth components
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   └── ProtectedRoute.tsx
│   │
│   ├── dashboard/                # Dashboard components
│   │   ├── DashboardLayout.tsx
│   │   ├── DashboardHeader.tsx
│   │   └── Sidebar.tsx
│   │
│   ├── assets/                   # Asset components
│   │   ├── AssetCard.tsx
│   │   ├── AssetGrid.tsx
│   │   ├── AssetFilters.tsx
│   │   ├── AssetUploader.tsx
│   │   └── ThreeDPreview.tsx     # React Three Fiber viewer
│   │
│   ├── devices/                  # Device components
│   │   ├── DeviceTable.tsx
│   │   ├── DeviceStatusBadge.tsx
│   │   ├── DeviceHealthCard.tsx
│   │   ├── DeviceCommandPanel.tsx
│   │   └── DeviceMap.tsx         # Location view
│   │
│   ├── playlists/                # Playlist components
│   │   ├── PlaylistCard.tsx
│   │   └── PlaylistEditor.tsx
│   │
│   ├── ui/                       # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── table.tsx
│   │   ├── tabs.tsx
│   │   ├── toast.tsx
│   │   └── ...
│   │
│   └── shared/                   # Shared components
│       └── providers.tsx         # React Query provider
│
├── lib/                          # Utilities & configs
│   ├── api/                      # API client
│   │   ├── client.ts             # Axios instance with interceptors
│   │   ├── auth.ts               # Auth API calls
│   │   ├── assets.ts             # Assets API calls
│   │   ├── devices.ts            # Devices API calls
│   │   ├── playlists.ts          # Playlists API calls
│   │   ├── organizations.ts      # Org API calls
│   │   └── users.ts              # Users API calls
│   │
│   ├── store/                    # Zustand stores
│   │   ├── authStore.ts          # Auth state
│   │   ├── organizationStore.ts  # Organization state
│   │   └── uiStore.ts            # UI state (sidebar, theme)
│   │
│   └── utils/
│       └── cn.ts                 # Class name merger
│
├── types/                        # TypeScript types
│   └── models.ts                 # Domain models (matching backend)
│
├── middleware.ts                 # Auth middleware
├── next.config.mjs               # Next.js configuration
├── tailwind.config.ts            # Tailwind configuration
├── tsconfig.json                 # TypeScript configuration
├── package.json                  # Dependencies
└── .env.local.example            # Environment variables template
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running (default: http://localhost:8000)

### Installation

1. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

2. **Configure environment variables**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your settings
   ```

3. **Start the development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000 (should be running separately)

## Environment Variables

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# S3/MinIO (for direct uploads)
NEXT_PUBLIC_S3_ENDPOINT=http://localhost:9000
NEXT_PUBLIC_S3_BUCKET=holohub-dev

# Map (optional)
NEXT_PUBLIC_MAPBOX_TOKEN=your-mapbox-token

# Analytics (optional)
NEXT_PUBLIC_GA_ID=

# Feature Flags
NEXT_PUBLIC_ENABLE_MAP_VIEW=true
NEXT_PUBLIC_ENABLE_3D_PREVIEW=true
```

## Key Features

### 1. Authentication Flow
- JWT with access/refresh tokens
- Automatic token refresh via axios interceptors
- MFA support (TOTP)
- Protected routes with middleware

### 2. Assets Library
- Grid/list view toggle
- Search with debounce
- Filter by category, status
- Sort by name, date, size
- Upload with drag-drop
- Real-time progress tracking

### 3. 3D Preview
- React Three Fiber integration
- GLB/GLTF file support
- Orbit controls for interaction
- Environment lighting
- Grid helper
- Loading and error states

### 4. Device Management
- Status indicators (online/offline)
- Health metrics visualization
- Remote command sending
- Location map view
- Real-time heartbeat updates

### 5. Playlist Editor
- Drag-drop reordering
- Duration per item
- Loop and shuffle modes
- Transition types
- Schedule configuration

## API Client

The API client is configured with axios and includes:

- **Request interceptor**: Adds auth token to all requests
- **Response interceptor**: Handles token refresh and error responses
- **Automatic retry**: On 401, attempts token refresh

```typescript
import { authApi, assetsApi } from "@/lib/api";

// Login
const response = await authApi.login({ email, password });

// List assets
const assets = await assetsApi.list({ page: 1, page_size: 20 });

// Get asset details
const asset = await assetsApi.get(assetId);
```

## State Management

### Zustand Stores

**Auth Store** (`lib/store/authStore.ts`):
- User data
- Access/refresh tokens
- Authentication status
- Persisted to localStorage

**Organization Store** (`lib/store/organizationStore.ts`):
- Current organization
- Organization stats

**UI Store** (`lib/store/uiStore.ts`):
- Sidebar state
- Theme (light/dark)
- View mode preferences

### React Query

Used for server state:
- Automatic caching and refetching
- Optimistic updates
- Pagination support
- Error handling

```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ["assets", filters],
  queryFn: () => assetsApi.list(filters),
});
```

## Deployment

### Vercel

1. **Connect repository**
   - Link your GitHub repository to Vercel

2. **Configure environment variables**
   - Set `NEXT_PUBLIC_API_URL` to production API

3. **Deploy**
   - Automatic deployments on push to main branch

### Build

```bash
npm run build
npm start
```

## Development

### Code Style

- **Prettier**: Code formatting
- **ESLint**: Linting
- **TypeScript**: Type checking

```bash
# Format code
npm run format

# Lint code
npm run lint

# Type check
npm run type-check
```

### Component Guidelines

1. **Use TypeScript** - All components should be typed
2. **Server components** - Use for data fetching when possible
3. **Client components** - Add `"use client"` for interactivity
4. **shadcn/ui** - Use provided UI components
5. **Lucide icons** - Consistent icon set

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

MIT License - see LICENSE file for details.
