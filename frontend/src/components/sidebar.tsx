"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { 
  LayoutDashboard, 
  Bot, 
  Activity, 
  LogOut,
  Menu
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { toast } from "sonner";
import { logout } from "@/utils/auth";

const navItems = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard
  },
  {
    name: "AI Agents",
    href: "/agents",
    icon: Bot
  },
  {
    name: "Traces",
    href: "/traces",
    icon: Activity
  }
];

interface SidebarNavItemProps {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  name: string;
}

function SidebarNavItem({ href, icon: Icon, name }: SidebarNavItemProps) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-2 rounded-lg px-3 py-2 text-gray-500 transition-all hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-50",
        isActive ? "bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-50" : ""
      )}
    >
      <Icon className="h-5 w-5" />
      <span>{name}</span>
    </Link>
  );
}

export function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  
  const handleSignOut = () => {
    // Use the logout function from auth utility
    logout();
    
    // Show notification
    toast.success("Signed out successfully");
  };
  
  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex h-screen w-60 flex-col border-r bg-background p-4">
        <div className="px-3 py-2">
          <h2 className="text-lg font-semibold tracking-tight">datagusto</h2>
        </div>
        <div className="mt-8 flex flex-1 flex-col gap-1">
          {navItems.map((item) => (
            <SidebarNavItem key={item.href} {...item} />
          ))}
        </div>
        <div className="mt-auto border-t pt-4">
          <Button 
            variant="outline" 
            className="w-full justify-start gap-2"
            onClick={handleSignOut}
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </Button>
        </div>
      </aside>

      {/* Mobile Sidebar */}
      <Sheet>
        <SheetTrigger asChild>
          <Button variant="outline" size="icon" className="md:hidden fixed top-4 left-4 z-40">
            <Menu className="h-5 w-5" />
            <span className="sr-only">Toggle Menu</span>
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-60 p-0">
          <div className="p-4 flex flex-col h-full">
            <div className="px-3 py-2">
              <h2 className="text-lg font-semibold tracking-tight">datagusto</h2>
            </div>
            <div className="mt-8 flex flex-1 flex-col gap-1">
              {navItems.map((item) => (
                <SidebarNavItem key={item.href} {...item} />
              ))}
            </div>
            <div className="mt-auto border-t pt-4">
              <Button 
                variant="outline" 
                className="w-full justify-start gap-2"
                onClick={handleSignOut}
              >
                <LogOut className="h-4 w-4" />
                Sign Out
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
} 