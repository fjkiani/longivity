import Link from "next/link";
import Logo from "./logo";

export default function Header() {
  return (
    <header className="fixed top-4 z-30 w-full">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="relative flex h-14 items-center justify-between gap-3 rounded-2xl bg-white/90 px-4 shadow-lg shadow-black/[0.03] backdrop-blur-sm border border-gray-200/60">
          <div className="flex flex-1 items-center">
            <Logo />
          </div>
          <nav className="hidden md:flex md:grow">
            <ul className="flex grow flex-wrap items-center justify-center gap-6 text-sm">
              <li>
                <Link href="/#platform" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">
                  Platform
                </Link>
              </li>
              <li>
                <Link href="/#science" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">
                  Science
                </Link>
              </li>
              <li>
                <Link href="/#workflow" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">
                  How It Works
                </Link>
              </li>
            </ul>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors hidden sm:block">
              Sign In
            </Link>
            <Link
              href="/login"
              className="px-4 py-2 rounded-xl bg-gray-900 hover:bg-black text-white text-sm font-bold transition-all shadow-sm hover:-translate-y-0.5"
            >
              Get Demo
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
