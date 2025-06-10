import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const TOKEN_KEY = 'access_token';

// 認証が必要なパスのパターン
const protectedRoutes: string[] = [];

export function middleware(request: NextRequest) {
  // 現在のパス
  const { pathname } = request.nextUrl;
  
  // 認証が必要なルートかチェック
  const isProtectedRoute = protectedRoutes.some(route => 
    pathname === route || pathname.startsWith(`${route}/`)
  );
  
  // Since we use localStorage for tokens, we can't check authentication state in middleware
  // We'll rely on client-side auth context for redirects
  // Only check authorization header for server-side requests
  const authHeader = request.headers.get('authorization');
  const hasAuthHeader = authHeader && authHeader.startsWith('Bearer ');
  
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Middleware] Path: ${pathname}`);
    console.log(`[Middleware] Auth Header: ${hasAuthHeader ? 'present' : 'absent'}`);
  }
  
  // Since we use localStorage for auth state, we can't reliably check authentication in middleware
  // Let the client-side auth context handle redirects
  
  return NextResponse.next();
}

// ミドルウェアを適用するパスを指定
export const config = {
  matcher: [
    /*
     * 以下に一致するパスでミドルウェアを実行:
     * - /
     * - /sign-in
     * - /sign-up
     */
    '/',
    '/sign-in',
    '/sign-up',
  ],
}; 