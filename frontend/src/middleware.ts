import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { ACCESS_TOKEN_KEY } from './utils/auth';

// 認証が必要なパスのパターン
const protectedRoutes = [
  '/dashboard',
  '/agents',
  '/sessions',
  '/traces',
  '/observations',
];

export function middleware(request: NextRequest) {
  // クッキーからセッション情報またはトークンを取得
  const sessionCookie = request.cookies.get('session');
  const tokenCookie = request.cookies.get(ACCESS_TOKEN_KEY);
  
  // 現在のパス
  const { pathname } = request.nextUrl;
  
  // For debugging - log the current path and cookies in development
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Middleware] Path: ${pathname}`);
    console.log(`[Middleware] Request URL: ${request.url}`);
    console.log(`[Middleware] Session Cookie: ${sessionCookie ? 'present' : 'absent'}`);
    console.log(`[Middleware] Token Cookie: ${tokenCookie ? 'present' : 'absent'}`);
    console.log(`[Middleware] All Cookies:`, request.cookies.getAll().map(c => c.name));
    
    // Log headers for debugging
    const headers = Object.fromEntries(request.headers);
    console.log(`[Middleware] Headers:`, JSON.stringify(headers, null, 2));
  }
  
  // 認証が必要なルートかチェック
  const isProtectedRoute = protectedRoutes.some(route => 
    pathname === route || pathname.startsWith(`${route}/`)
  );
  
  // 認証状態 - also check authorization header for token
  const authHeader = request.headers.get('authorization');
  const hasAuthHeader = authHeader && authHeader.startsWith('Bearer ');
  const isAuthenticated = !!sessionCookie || !!tokenCookie || hasAuthHeader;
  
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Middleware] Auth Header: ${hasAuthHeader ? 'present' : 'absent'}`);
    console.log(`[Middleware] Is Authenticated: ${isAuthenticated}`);
  }
  
  // 認証が必要なパスだが認証されていない場合、サインインにリダイレクト
  if (isProtectedRoute && !isAuthenticated) {
    const redirectUrl = new URL('/sign-in', request.url);
    return NextResponse.redirect(redirectUrl);
  }
  // サインイン・サインアップページにアクセスしたが既に認証済みの場合、ダッシュボードにリダイレクト
  if ((pathname === '/sign-in' || pathname === '/sign-up') && isAuthenticated) {
    const redirectUrl = new URL('/dashboard', request.url);
    return NextResponse.redirect(redirectUrl);
  }
  
  // ルートパスへのアクセスをリダイレクト
  if (pathname === '/') {
    if (isAuthenticated) {
      const redirectUrl = new URL('/dashboard', request.url);
      return NextResponse.redirect(redirectUrl);
    } else {
      const redirectUrl = new URL('/sign-in', request.url);
      return NextResponse.redirect(redirectUrl);
    }
  }
  
  return NextResponse.next();
}

// ミドルウェアを適用するパスを指定
export const config = {
  matcher: [
    /*
     * 以下に一致するパスでミドルウェアを実行:
     * - /
     * - /dashboard, /dashboard/任意のパス
     * - /agents, /agents/任意のパス
     * - /sessions, /sessions/任意のパス
     * - /traces, /traces/任意のパス
     * - /observations, /observations/任意のパス
     * - /organizations, /organizations/任意のパス
     * - /users, /users/任意のパス
     * - /sign-in
     * - /sign-up
     */
    '/',
    '/dashboard/:path*',
    '/agents/:path*',
    '/sessions/:path*',
    '/traces/:path*',
    '/observations/:path*',
    '/sign-in',
    '/sign-up',
  ],
}; 