import Logo from "@/components/apx/logo";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 bg-surface/60 backdrop-blur-xl border-b border-white/5">
      <div className="h-14 flex items-center px-4 sm:px-6 max-w-6xl mx-auto">
        <Logo />
      </div>
    </header>
  );
}

export default Navbar;
