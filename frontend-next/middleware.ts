import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Next.js中间件 - 路由守卫
 * 保护需要登录的页面
 */
export function middleware(request: NextRequest) {
  // 获取Token（从localStorage无法在middleware中直接访问，需要通过cookie）
  // 注意：这里暂时跳过认证检查，因为需要配合登录页面保存cookie
  // 实际生产环境中，应该在登录成功后将token也保存到httpOnly cookie中

  const isLoginPage = request.nextUrl.pathname.startsWith('/login');
  const isOAuthCallback = request.nextUrl.pathname.startsWith('/oauth/callback');
  const isPublicPath = isLoginPage || isOAuthCallback;

  // 暂时注释掉强制登录逻辑，因为我们还在开发阶段
  // 等前端和后端都完善后再启用

  // const token = request.cookies.get('access_token')?.value;

  // // 未登录且不是公开路径，跳转到登录页
  // if (!token && !isPublicPath) {
  //   const loginUrl = new URL('/login', request.url);
  //   loginUrl.searchParams.set('redirect', request.nextUrl.pathname);
  //   return NextResponse.redirect(loginUrl);
  // }

  // // 已登录且访问登录页，跳转到首页
  // if (token && isLoginPage) {
  //   return NextResponse.redirect(new URL('/', request.url));
  // }

  return NextResponse.next();
}

/**
 * 配置需要应用中间件的路径
 * 排除静态资源和API路由
 */
export const config = {
  matcher: [
    /*
     * 匹配所有请求路径，除了：
     * - api (API routes)
     * - _next/static (静态文件)
     * - _next/image (图片优化)
     * - favicon.ico (网站图标)
     * - public文件 (public目录下的静态资源)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|icons|images).*)',
  ],
};

