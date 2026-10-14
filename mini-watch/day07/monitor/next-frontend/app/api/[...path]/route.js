// 지원 코드: 브라우저의 같은 주소 /api 요청을 감시 Flask로 전달한다.
export const runtime = 'nodejs';

async function forward(request, context) {
  const { path } = await context.params;
  // 앱 화면이 사용하는 경로만 전달한다. 이벤트 수신 POST는 일반 서버 전용이다.
  const resource = path.join('/');
  const allowed = /^(auth\/(me|login|logout)|events|notes(\/\d+)?|sentry-test)$/.test(resource);
  if (!allowed || (resource === 'events' && request.method !== 'GET')) {
    return Response.json({ error: '지원하지 않는 API 요청입니다.' }, { status: 404 });
  }
  const base = process.env.MONITOR_API_URL;
  if (!base) {
    return Response.json({ error: 'MONITOR_API_URL을 설정해 주세요.' }, { status: 503 });
  }
  try {
    const target = new URL('/api/' + path.map(encodeURIComponent).join('/'), base);
    if (!['http:', 'https:'].includes(target.protocol)) throw new Error('Invalid API URL');
    target.search = new URL(request.url).search;
    const headers = new Headers();
    for (const name of ['content-type', 'cookie', 'x-csrf-token']) {
      const value = request.headers.get(name);
      if (value) headers.set(name, value);
    }
    const options = {
      method: request.method,
      headers,
      cache: 'no-store',
      redirect: 'manual',
      signal: AbortSignal.timeout(15000),
    };
    if (!['GET', 'HEAD'].includes(request.method)) options.body = await request.arrayBuffer();
    const upstream = await fetch(target, options);
    const responseHeaders = new Headers({ 'Cache-Control': 'no-store' });
    const contentType = upstream.headers.get('content-type');
    if (contentType) responseHeaders.set('Content-Type', contentType);
    // 로그인 응답의 쿠키를 브라우저에 전달해야 다음 요청에서 로그인 상태가 유지된다.
    for (const cookie of upstream.headers.getSetCookie()) responseHeaders.append('Set-Cookie', cookie);
    const body = [204, 205, 304].includes(upstream.status) ? null : await upstream.arrayBuffer();
    return new Response(body, { status: upstream.status, headers: responseHeaders });
  } catch {
    return Response.json(
      { error: '감시 API에 연결하지 못했습니다. /health와 MONITOR_API_URL을 확인해 주세요.' },
      { status: 502 },
    );
  }
}

export { forward as GET, forward as POST, forward as PUT, forward as DELETE };
