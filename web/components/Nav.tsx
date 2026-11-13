import Link from "next/link";

const links = [
  ["/", "Today"],
  ["/front-desk", "Front Desk"],
  ["/shelf", "Shelf"],
  ["/reviews", "Reviews"],
  ["/orders", "Orders"],
  ["/agents", "Agent feed"],
];

export default function Nav() {
  return (
    <header className="border-b border-cedar-100 bg-white">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-6 py-4">
        <div>
          <div className="text-xl font-bold text-cedar-800">Cedar &amp; Date Market</div>
          <div className="text-sm text-stone-500">Rafi · Your shop&apos;s AI crew</div>
        </div>
        <nav className="flex flex-wrap gap-1">
          {links.map(([href, label]) => (
            <Link key={href} href={href} className="rounded-lg px-3 py-1.5 text-sm font-medium text-cedar-700 hover:bg-cedar-50">
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
