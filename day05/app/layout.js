import Link from "next/link";
import "./globals.css";

export const metadata = {
  title: "Next.js 메모 앱",
  description: "Next.js App Router 기반 메모 및 카운터 애플리케이션",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>
        <header>
          <nav>
            <Link href="/">홈</Link>
            <Link href="/notes">메모</Link>
          </nav>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
