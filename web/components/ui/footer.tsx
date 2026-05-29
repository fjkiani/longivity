import Link from "next/link";
import Logo from "./logo";

export default function Footer({ border = false }: { border?: boolean }) {
  return (
    <footer className={`${border ? "border-t border-gray-200" : ""}`}>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div className="col-span-2 md:col-span-1 space-y-3">
            <Logo />
            <p className="text-sm text-gray-500 leading-relaxed">
              Clinical intelligence for longevity medicine. One decision per patient, every time.
            </p>
            <p className="text-xs text-gray-400">© Built by JediLabs.org.</p>
          </div>
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-900">Platform</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/#platform" className="text-gray-500 hover:text-gray-900 transition-colors">How It Works</Link></li>
              <li><Link href="/#science" className="text-gray-500 hover:text-gray-900 transition-colors">The Science</Link></li>
              <li><Link href="/login" className="text-gray-500 hover:text-gray-900 transition-colors">Sign In</Link></li>
            </ul>
          </div>
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-900">Company</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/about" className="text-gray-500 hover:text-gray-900 transition-colors">About</Link></li>
              <li><a href="mailto:jedi@jedilabs.org" className="text-gray-500 hover:text-gray-900 transition-colors">Contact</a></li>
            </ul>
          </div>
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-900">Legal</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/privacy" className="text-gray-500 hover:text-gray-900 transition-colors">Privacy Policy</Link></li>
              <li><Link href="/terms" className="text-gray-500 hover:text-gray-900 transition-colors">Terms of Service</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-10 pt-6 border-t border-gray-100">
          <p className="text-xs text-gray-400 text-center">
            Research Use Only (RUO). Longevity is not a medical device and is not intended for clinical diagnosis, treatment, or prevention of disease.
          </p>
        </div>
      </div>
    </footer>
  );
}
