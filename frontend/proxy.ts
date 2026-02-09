
import createMiddleware from 'next-intl/middleware';
import { NextRequest, NextResponse } from 'next/server';
import { routing } from './i18n/routing';

const intlMiddleware = createMiddleware(routing);

export default function proxy(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Special handling for root path redirect
    if (pathname === '/') {
        // Redirect / to /en (as per requirement: App defaults to English)
        return NextResponse.redirect(new URL('/en', request.url));
    }

    // Special handling for /login redirect
    if (pathname === '/login') {
        // Redirect /login to /fr/login (as per requirement: Login defaults to French)
        return NextResponse.redirect(new URL('/fr/login', request.url));
    }

    return intlMiddleware(request);
}

export const config = {
    // Match only internationalized pathnames
    matcher: ['/', '/(fr|en)/:path*', '/login']
};
